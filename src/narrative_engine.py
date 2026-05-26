import os
import json
import numpy as np
from groq import Groq

LEVEL_DESC = {
    'AMAN'    : 'kondisi pariwisata normal, tidak ada indikasi krisis',
    'WASPADA' : 'ada sinyal awal yang perlu dipantau',
    'SIAGA'   : 'tekanan signifikan pada sektor pariwisata',
    'KRISIS'  : 'krisis pariwisata yang membutuhkan respons segera'
}

def build_context(pred_row: dict, history_rows: list = None) -> dict:
    ctx = {
        'month'        : str(pred_row.get('month', 'N/A')),
        'crisis_score' : round(float(pred_row.get('crisis_score_100', 0)), 1),
        'crisis_level' : str(pred_row.get('crisis_level', 'WASPADA')),
        'rf_predicted' : str(pred_row.get('rf_predicted_level', 'N/A')),
        'rf_confidence': round(float(pred_row.get('rf_confidence', 0)) * 100, 1),
        'is_anomaly'   : int(pred_row.get('iso_anomaly', 0)),
        'wisman'       : int(pred_row.get('wisman', 0)),
        'tpk_bintang'  : round(float(pred_row.get('tpk_bintang', 0)), 1),
        'inflasi'      : round(float(pred_row.get('inflasi_processed', 0)), 2),
        'usd_idr'      : round(float(pred_row.get('usd_idr_avg', 0)), 0),
        'sentiment'    : round(float(pred_row.get('avg_sentiment_monthly', 0)), 3),
        'prob_krisis'  : round(float(pred_row.get('prob_krisis', 0)) * 100, 1),
        'prob_siaga'   : round(float(pred_row.get('prob_siaga', 0)) * 100, 1),
        'bali_share'   : round(float(pred_row.get('bali_share_pct', 0)), 1),
        'wisman_zscore': round(float(pred_row.get('wisman_zscore', 0)), 2),
    }
    if history_rows and len(history_rows) >= 2:
        avg3 = np.mean([r.get('wisman', 0) for r in history_rows[-3:]])
        ctx['wisman_trend']  = 'naik' if ctx['wisman'] > avg3 else 'turun'
        ctx['avg_wisman_3m'] = round(avg3, 0)
        ctx['prev_levels']   = [r.get('crisis_level', 'N/A') for r in history_rows[-3:]]
    else:
        ctx['wisman_trend']  = 'tidak tersedia'
        ctx['avg_wisman_3m'] = 0
        ctx['prev_levels']   = []
    return ctx

def build_prompt(ctx: dict, report_type: str = 'summary') -> str:
    level_text = LEVEL_DESC.get(ctx['crisis_level'], ctx['crisis_level'])
    prev = ' -> '.join(ctx['prev_levels']) if ctx['prev_levels'] else 'N/A'
    data_block = (
        f"DATA PARIWISATA BALI - {ctx['month']}\n"
        f"Crisis Score: {ctx['crisis_score']}/100 -> Level {ctx['crisis_level']} ({level_text})\n"
        f"Prediksi RF: {ctx['rf_predicted']} (confidence: {ctx['rf_confidence']}%)\n"
        f"Anomali: {'Ya' if ctx['is_anomaly'] else 'Tidak'} | P(Krisis): {ctx['prob_krisis']}% | P(Siaga): {ctx['prob_siaga']}%\n"
        f"Wisman: {ctx['wisman']:,.0f} (trend: {ctx['wisman_trend']}, avg 3bln: {int(ctx['avg_wisman_3m']):,.0f})\n"
        f"Pangsa Bali: {ctx['bali_share']}% | Z-score: {ctx['wisman_zscore']}\n"
        f"TPK Hotel: {ctx['tpk_bintang']}% | USD/IDR: Rp {int(ctx['usd_idr']):,}\n"
        f"Inflasi: {ctx['inflasi']}% | Sentimen: {ctx['sentiment']}\n"
        f"Histori: {prev}\n"
    )
    if report_type == 'summary':
        return ("Kamu adalah analis BaliGuard (early warning pariwisata Bali).\n"
                + data_block
                + f"Buat ringkasan kondisi pariwisata Bali bulan {ctx['month']} "
                "dalam 2-3 kalimat Bahasa Indonesia. Tajam, berbasis data, cocok untuk KPI card.")
    elif report_type == 'alert':
        return ("Kamu adalah sistem BaliGuard. Kondisi kritis terdeteksi.\n"
                + data_block
                + "Buat PERINGATAN DARURAT (max 120 kata) Bahasa Indonesia: "
                "status level, top 3 indikator kritis, 1 rekomendasi tindakan segera.")
    else:
        return ("Kamu adalah analis BaliGuard.\n"
                + data_block
                + "Buat laporan bulanan Bahasa Indonesia:\n"
                "1. Ringkasan Eksekutif (2-3 kalimat)\n"
                "2. Analisis Indikator (3-4 kalimat)\n"
                "3. Faktor Pendorong (2-3 kalimat)\n"
                "4. Rekomendasi (3 poin konkret)")

def generate(pred_row: dict, report_type: str = 'summary',
             api_key: str = None, history_rows: list = None) -> dict:
    if api_key is None:
        api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key:
        return {'success': False, 'narrative': '[API key tidak dikonfigurasi]', 'error': 'No API key'}
    try:
        ctx      = build_context(pred_row, history_rows)
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model       = 'llama-3.3-70b-versatile',
            messages    = [{'role': 'user', 'content': build_prompt(ctx, report_type)}],
            temperature = 0.7,
            max_tokens  = 1024
        )
        return {
            'success'      : True,
            'narrative'    : response.choices[0].message.content,
            'tokens'       : response.usage.prompt_tokens + response.usage.completion_tokens,
            'month'        : ctx['month'],
            'crisis_level' : ctx['crisis_level'],
        }
    except Exception as e:
        return {'success': False, 'narrative': f'[Error: {e}]', 'error': str(e)}

def load_cache(cache_path: str = 'data/final/narratives_cache.json') -> dict:
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}
