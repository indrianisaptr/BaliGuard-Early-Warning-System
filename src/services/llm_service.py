"""
src/services/llm_service.py — BaliGuard: LLM / Groq Service
Semua interaksi dengan Groq API dan Anthropic API ada di sini.
"""
import os, json, time, requests
import streamlit as st
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────
GROQ_ENDPOINT  = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL     = 'llama3-8b-8192'
ANTHROPIC_MODEL = 'claude-sonnet-4-5'
CACHE_PATH     = Path('data/final/narratives_cache.json')

LEVEL_DESC = {
    'AMAN':    'kondisi pariwisata normal dan stabil',
    'WASPADA': 'tanda-tanda perlambatan mulai terdeteksi, perlu pemantauan',
    'SIAGA':   'tekanan signifikan pada sektor pariwisata, diperlukan respons',
    'KRISIS':  'krisis pariwisata aktif, diperlukan intervensi segera',
}


def _get_groq_key() -> str:
    k = os.environ.get('GROQ_API_KEY', '')
    if not k:
        try: k = st.secrets.get('GROQ_API_KEY', '')
        except Exception: pass
    return k


def _get_anthropic_key() -> str:
    k = os.environ.get('ANTHROPIC_API_KEY', '')
    if not k:
        try: k = st.secrets.get('ANTHROPIC_API_KEY', '')
        except Exception: pass
    return k


# ── Prompt Builders ───────────────────────────────────────────────────
def build_narrative_prompt(ctx: dict, mode: str = 'executive') -> str:
    """
    Bangun prompt untuk narasi. mode ∈ {'executive','alert','recommendation'}
    ctx harus berisi: sel, level, score, wisman, tpk, inflasi, usd_avg,
                      sent, rf_pred, conf, delta_ctx
    """
    sel    = ctx.get('sel', '')
    level  = ctx.get('level', 'AMAN')
    score  = ctx.get('score', 0)
    desc   = LEVEL_DESC.get(level, '')
    d      = ctx.get('delta_ctx', {})

    # Kalkulasi delta MoM
    def _delta(key):
        if key in d:
            v = d[key]
            return f"{v['curr']:,.0f} (delta: {v['delta']:+,.0f}, {v['delta_pct']:+.1f}%)"
        return 'N/A'

    base_context = f"""
DATA DASHBOARD BALIGUARD — {sel}
=========================================
Crisis Score   : {score:.1f}/100
Level          : {level} ({desc})
RF Prediction  : {ctx.get('rf_pred','-')} (confidence {ctx.get('conf',0)*100:.0f}%)
Anomali        : {'TERDETEKSI' if ctx.get('is_anom') else 'Tidak'}

INDIKATOR UTAMA (MoM):
- Wisman        : {_delta('wisman')}
- TPK Bintang   : {_delta('tpk_bintang')}%
- Inflasi Bali  : {_delta('inflasi_processed')}%
- USD/IDR       : {_delta('usd_idr_avg')}
- Sentimen      : {_delta('avg_sentiment_monthly')}
- Bali Share    : {_delta('bali_share_pct')}%
"""

    if mode == 'executive':
        return (
            "Anda adalah analis risiko pariwisata senior Bali. "
            "Berdasarkan data berikut, tulis EXECUTIVE SUMMARY dalam Bahasa Indonesia "
            "yang padat (3-4 paragraf). Fokus pada: (1) kondisi terkini, "
            "(2) faktor pendorong utama, (3) tren yang perlu diwaspadai. "
            "Gunakan bahasa formal namun mudah dipahami pejabat pariwisata.\n\n"
            + base_context
        )
    elif mode == 'alert':
        return (
            "Anda adalah sistem peringatan dini pariwisata Bali. "
            f"Level saat ini adalah {level}. "
            "Buat EMERGENCY ALERT dalam Bahasa Indonesia yang singkat (2-3 paragraf). "
            "Sertakan: kondisi kritis, penyebab utama, dan tindakan mendesak. "
            "Gunakan bahasa tegas dan to-the-point.\n\n"
            + base_context
        )
    elif mode == 'recommendation':
        return (
            "Anda adalah konsultan strategi pariwisata Bali. "
            "Berdasarkan data berikut, berikan REKOMENDASI KEBIJAKAN dalam Bahasa Indonesia "
            "(minimal 4 poin spesifik) untuk Dinas Pariwisata Bali. "
            "Setiap rekomendasi harus actionable dan berbasis data.\n\n"
            + base_context
        )
    elif mode == 'swot':
        return (
            "Anda adalah analis strategis pariwisata. "
            "Buat ANALISIS SWOT pariwisata Bali berdasarkan data berikut dalam Bahasa Indonesia. "
            "Format: Kekuatan | Kelemahan | Peluang | Ancaman, masing-masing 2-3 poin.\n\n"
            + base_context
        )
    return base_context


# ── API Callers ───────────────────────────────────────────────────────
def call_groq(prompt: str, max_tokens: int = 800,
              temperature: float = 0.7) -> str:
    """Kirim prompt ke Groq API, return teks respons."""
    key = _get_groq_key()
    if not key:
        return '⚠️ GROQ_API_KEY tidak ditemukan di .env atau st.secrets'

    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    payload = {
        'model': GROQ_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }
    try:
        r = requests.post(GROQ_ENDPOINT, headers=headers,
                          json=payload, timeout=30)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return '⚠️ Groq API timeout. Coba lagi.'
    except Exception as e:
        return f'⚠️ Groq API error: {e}'


def call_anthropic(prompt: str, max_tokens: int = 1000) -> str:
    """Kirim prompt ke Anthropic Claude API via Anthropic SDK."""
    key = _get_anthropic_key()
    if not key:
        return '⚠️ ANTHROPIC_API_KEY tidak ditemukan'
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return msg.content[0].text
    except Exception as e:
        return f'⚠️ Anthropic API error: {e}'


# ── Cache ─────────────────────────────────────────────────────────────
def load_narrative_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_narrative_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_or_generate(cache: dict, month: str, mode: str,
                    ctx: dict, provider: str = 'groq') -> tuple[str, bool]:
    """
    Cek cache dulu. Jika miss, generate via API.
    Return: (teks_narasi, from_cache)
    """
    cache_key = f"{month}_{mode}"
    if cache_key in cache:
        return cache[cache_key], True

    prompt = build_narrative_prompt(ctx, mode=mode)
    if provider == 'anthropic':
        text = call_anthropic(prompt)
    else:
        text = call_groq(prompt)

    if not text.startswith('⚠️'):
        cache[cache_key] = text
        save_narrative_cache(cache)

    return text, False
