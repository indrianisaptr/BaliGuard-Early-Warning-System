"""
src/services/llm_service.py — BaliGuard: LLM / Groq Service
Semua interaksi dengan Groq API dan Anthropic API ada di sini.
"""
import os, json, re, time, requests
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

LANG_GUARD = (
    "ATURAN BAHASA (WAJIB DIPATUHI, PRIORITAS TERTINGGI):\n"
    "1. Seluruh jawaban HARUS ditulis 100% dalam Bahasa Indonesia formal yang natural, "
    "dari kata pertama hingga kata terakhir.\n"
    "2. DILARANG KERAS menyisipkan aksara atau karakter non-Latin dalam bentuk apa pun "
    "(termasuk Hanzi/Mandarin seperti 处于, 此外, 因此, 同时, aksara Jepang, Korea, Arab, "
    "Cyrillic, atau aksara lainnya), baik berupa kata, frasa, maupun karakter tunggal "
    "yang terselip di antara kata-kata Indonesia.\n"
    "3. DILARANG mencampur Bahasa Indonesia dengan bahasa asing lain di luar istilah "
    "teknis yang memang umum dipakai dalam Bahasa Indonesia.\n"
    "4. Istilah teknis berbahasa Inggris yang TIDAK memiliki padanan umum dalam Bahasa "
    "Indonesia (misalnya: Random Forest, External Risk, Physical Risk, Media Risk, "
    "Crisis Score) BOLEH digunakan apa adanya, tetapi struktur kalimat di sekitarnya "
    "tetap harus Bahasa Indonesia.\n"
    "5. SELF-CHECK SEBELUM MENJAWAB: sebelum mengeluarkan jawaban final, periksa ulang "
    "seluruh draf secara internal. Jika ditemukan satu pun karakter non-Latin atau kata "
    "dari bahasa lain (Mandarin/Jepang/Korea/Arab/dst), perbaiki dan gantikan dengan "
    "padanan Bahasa Indonesia yang tepat SEBELUM menampilkan jawaban. Jangan tampilkan "
    "proses koreksi ini ke pengguna — tampilkan hanya hasil akhir yang sudah bersih "
    "dan 100% Bahasa Indonesia.\n\n"
)

LANG_GUARD_REMINDER = (
    "\n\nPENGINGAT TERAKHIR (paling penting): tulis ulang jawaban Anda di atas, "
    "pastikan SELURUHNYA Bahasa Indonesia formal dan TIDAK ADA satu pun karakter "
    "Mandarin, Jepang, Korea, Arab, atau aksara non-Latin lain yang tersisip. "
    "Jika ada, hapus/gantikan dengan kata Bahasa Indonesia sebelum menjawab."
)

# Pola untuk menyaring aksara non-Latin sebagai jaring pengaman terakhir
NON_LATIN_PATTERN = re.compile(
    r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7a3\u0600-\u06ff\u0400-\u04ff]+'
)

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

SKOR RISIKO EKSTERNAL:
- Physical Risk    : {ctx.get('physical_risk_score', 0):.1f}/100
- Media Risk       : {ctx.get('media_risk_score', 0):.1f}/100
- Tourist Percep   : {ctx.get('tourist_perception_score', 0):.1f}/100
- External Risk    : {ctx.get('external_risk_score', 0):.1f}/100
"""

    if mode == 'executive':
        return (
            LANG_GUARD +
            "Anda adalah analis risiko pariwisata senior Bali. "
            "Berdasarkan data berikut, tulis EXECUTIVE SUMMARY dalam Bahasa Indonesia "
            "yang padat (3-4 paragraf). Fokus pada: (1) kondisi terkini, "
            "(2) faktor pendorong utama termasuk risiko eksternal yang paling dominan, "
            "(3) apakah risiko berasal dari bencana/cuaca, pemberitaan media global, "
            "atau penurunan persepsi wisatawan, dan dampaknya terhadap pariwisata Bali. "
            "Gunakan bahasa formal namun mudah dipahami pejabat pariwisata.\n\n"
            + base_context
            + LANG_GUARD_REMINDER
        )
    elif mode == 'alert':
        return (
            LANG_GUARD +
            "Anda adalah sistem peringatan dini pariwisata Bali. "
            f"Level saat ini adalah {level}. "
            "Buat EMERGENCY ALERT dalam Bahasa Indonesia yang singkat (2-3 paragraf). "
            "Sertakan: kondisi kritis, identifikasi apakah ancaman utama berasal dari "
            "risiko fisik (bencana/cuaca), risiko media (pemberitaan negatif global), "
            "atau penurunan persepsi wisatawan, serta tindakan mendesak yang spesifik. "
            "Gunakan bahasa tegas dan to-the-point.\n\n"
            + base_context
            + LANG_GUARD_REMINDER
        )
    elif mode == 'recommendation':
        return (
            LANG_GUARD +
            "Anda adalah konsultan strategi pariwisata Bali. "
            "Berdasarkan data berikut, berikan REKOMENDASI KEBIJAKAN dalam Bahasa Indonesia "
            "(minimal 4 poin spesifik) untuk Dinas Pariwisata Bali. "
            "Sertakan rekomendasi yang merespons faktor eksternal dominan — "
            "apakah itu mitigasi bencana, manajemen reputasi media internasional, "
            "atau strategi menarik wisatawan dari negara yang ekonominya sedang melemah. "
            "Setiap rekomendasi harus actionable dan berbasis data.\n\n"
            + base_context
            + LANG_GUARD_REMINDER
        )
    elif mode == 'swot':
        return (
            LANG_GUARD +
            "Anda adalah analis strategis pariwisata. "
            "Buat ANALISIS SWOT pariwisata Bali berdasarkan data berikut dalam Bahasa Indonesia. "
            "Format: Kekuatan | Kelemahan | Peluang | Ancaman, masing-masing 2-3 poin. "
            "Gunakan skor berikut untuk menentukan kuadran:\n"
            f"- Physical Risk {ctx.get('physical_risk_score',0):.1f}/100 → Ancaman fisik/bencana\n"
            f"- Media Risk {ctx.get('media_risk_score',0):.1f}/100 → Ancaman reputasi media global\n"
            f"- Tourist Perception {ctx.get('tourist_perception_score',0):.1f}/100 → "
            f"{'Peluang' if ctx.get('tourist_perception_score',0) >= 60 else 'Ancaman'} persepsi wisatawan\n"
            f"- External Risk {ctx.get('external_risk_score',0):.1f}/100 → faktor strategis utama\n\n"
            + base_context
            + LANG_GUARD_REMINDER
        )
    return LANG_GUARD + base_context


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

    if not text.startswith('⚠️') and NON_LATIN_PATTERN.search(text):
        text = NON_LATIN_PATTERN.sub('', text)
        text = re.sub(r' {2,}', ' ', text).strip()

    if not text.startswith('⚠️'):
        cache[cache_key] = text
        save_narrative_cache(cache)

    return text, False
