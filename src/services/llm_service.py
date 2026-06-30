"""
src/services/llm_service.py — BaliGuard: LLM Service Layer
Tanggung jawab:
  1. Membangun prompt untuk setiap tipe laporan
  2. Memanggil Groq API
  3. Post-processing output (CJK safety net)
  4. Cache management

TIDAK ada logika UI, TIDAK ada st.* di sini.
"""
import os, json, re, requests
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────
GROQ_ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions'
CACHE_PATH    = Path('data/final/narratives_cache.json')

LEVEL_DESC = {
    'AMAN':    'kondisi pariwisata normal',
    'WASPADA': 'ada sinyal awal yang perlu dipantau',
    'SIAGA':   'tekanan signifikan pada sektor pariwisata',
    'KRISIS':  'krisis pariwisata yang membutuhkan respons segera',
}

NON_LATIN_PATTERN = re.compile(
    r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff'
    r'\uac00-\ud7a3\u0600-\u06ff\u0400-\u04ff]+'
)
CJK_FIXES = {
    '处于': ' berada pada', '此外': ' Selain itu,',
    '因此': ' Oleh karena itu,', '同时': ' Sementara itu,',
}

NARASI_RULE = (
    "\n\nATURAN NARASI WAJIB (berlaku untuk SELURUH indikator risk score):\n"
    "Jangan hanya menyebut nilai angka. Setiap indikator risk score WAJIB dijelaskan dengan pola berikut:\n"
    "  [Nama indikator] berada pada level [Rendah/Sedang/Tinggi] ([nilai]/100), "
    "yang menunjukkan [arti indikator tersebut], sehingga [dampak konkret terhadap pariwisata Bali].\n\n"

    "Contoh BENAR (pola kalimat ilustratif — JANGAN salin angka contoh, WAJIB gunakan nilai aktual dari data):\n"
    "  'Media Risk berada pada level [nilai aktual]/100 [kategori], yang menunjukkan adanya risiko pemberitaan "
    "negatif di media internasional, sehingga dapat menekan kepercayaan wisatawan mancanegara "
    "terhadap Bali sebagai destinasi yang aman.'\n\n"
    "  'Tourist Perception berada pada level [nilai aktual]/100 [kategori], yang menunjukkan bahwa wisatawan "
    "memiliki persepsi tertentu terhadap Bali, sehingga memengaruhi pertumbuhan kunjungan dan "
    "belanja wisata dalam jangka pendek.'\n\n"
    "  'External Risk berada pada level [nilai aktual]/100 [kategori], yang menunjukkan tekanan eksternal "
    "berada pada kondisi tertentu, namun perlu dipantau karena dapat memengaruhi kestabilan "
    "kunjungan dalam beberapa bulan ke depan.'\n\n"

    "Contoh SALAH (DILARANG):\n"
    "  'Media Risk sebesar [angka]/100.' (tanpa kategori dan penjelasan dampak)\n"
    "  'Physical Risk Score: [angka]/100.' (hanya skor tanpa narasi sebab-akibat)\n"
    "  'External Risk berada di angka [angka].' (tanpa skala /100 dan kategori)\n\n"

    "PERINGATAN KERAS: [nilai aktual] dan [kategori] di atas adalah placeholder, BUKAN angka final. "
    "WAJIB diganti dengan nilai skor dan kategori SESUNGGUHNYA dari data aktual di atas.\n\n"

    "Panduan makna tiap indikator:\n"
    "  - Physical Risk → risiko dari bencana alam, cuaca ekstrem, dan gangguan fisik destinasi\n"
    "  - Media Risk → risiko dari pemberitaan negatif global yang merusak citra Bali\n"
    "  - Tourist Perception → tingkat kepercayaan dan persepsi positif wisatawan terhadap Bali\n"
    "  - External Risk → tekanan eksternal komposit (ekonomi global, geopolitik, dll) yang memengaruhi pariwisata\n"

    "\n\n================================================================\n"
    "ATURAN BAHASA — WAJIB DIPATUHI TANPA PENGECUALIAN:\n"
    "================================================================\n"
    "1. SELURUH output WAJIB menggunakan Bahasa Indonesia formal yang natural.\n"
    "2. DILARANG KERAS menggunakan karakter non-Latin: tidak boleh ada karakter "
    "Mandarin (汉字), Jepang (かな/カナ), Korea (한글), Arab (عربي), "
    "Cyrillic, atau aksara non-Latin lainnya.\n"
    "3. DILARANG mencampur bahasa: tidak boleh ada kata/frasa bahasa Mandarin, "
    "Jepang, Korea, Arab, Prancis, Spanyol, atau bahasa selain Indonesia dan "
    "istilah teknis Inggris yang lazim.\n"
    "4. Istilah teknis tanpa padanan umum (Random Forest, External Risk, Crisis Score, TPK) "
    "BOLEH tetap dalam bahasa Inggris, namun seluruh kalimat harus tetap berbahasa Indonesia.\n"
    "5. SELF-CHECK WAJIB: Sebelum output akhir, periksa ulang seluruh teks. "
    "Jika ditemukan karakter non-Latin atau kata asing di luar pengecualian di atas, "
    "ganti dengan padanan Bahasa Indonesia.\n"
    "================================================================\n"
)

FORMAT_STYLE_RULE = {
    'paragraf': (
        "\n\n=== FORMAT OUTPUT WAJIB: PARAGRAF ===\n"
        "Tulis seluruh isi setiap bagian dalam bentuk PARAGRAF NARATIF yang mengalir, "
        "bukan bullet/list. Heading bagian (**JUDUL**) tetap boleh dipakai sesuai struktur, "
        "tapi isi di bawah tiap heading harus berupa kalimat-kalimat tersambung, bukan baris per baris.\n"
        "DILARANG memakai tanda '-' atau angka '1.' '2.' di awal baris untuk isi bagian.\n"
    ),
    'poin': (
        "\n\n=== FORMAT OUTPUT WAJIB: POIN/BULLET ===\n"
        "Tulis seluruh isi setiap bagian dalam bentuk BULLET LIST ('- ' di awal baris), "
        "singkat dan padat per poin (maks 2 kalimat per poin). Heading bagian (**JUDUL**) tetap dipakai, "
        "tapi isi di bawahnya WAJIB berupa daftar poin, BUKAN paragraf panjang.\n"
    ),
}

# ── Data block builder ────────────────────────────────────────────────
def build_data_block(ctx: dict) -> str:
    """
    Bangun blok data terstruktur dari ctx dict.
    Dipanggil oleh semua prompt builder.
    """
    lv_text = LEVEL_DESC.get(ctx['crisis_level'], ctx['crisis_level'])
    prev    = ' -> '.join(ctx.get('prev_levels', [])) or 'N/A'

    contradiction = ""
    wd  = ctx.get('wisman_delta_pct', 0)
    sd  = ctx.get('sent_delta', 0)
    scd = ctx.get('score_delta', 0)
    if wd < -5 and sd > 0.05:
        contradiction = "KONTRADIKSI: Wisman turun tapi sentimen naik — kemungkinan tekanan dari faktor akses/ekonomi bukan kepuasan."
    elif wd > 5 and sd < -0.05:
        contradiction = "KONTRADIKSI: Wisman naik tapi sentimen turun — perlu investigasi kualitas layanan."
    elif scd > 5 and sd > 0.1:
        contradiction = "KONTRADIKSI: Crisis score memburuk tapi sentimen publik positif — tekanan mungkin struktural."

    block = (
        f"DATA PARIWISATA BALI — {ctx['month']}\n"
        f"Crisis Score: {ctx['crisis_score']}/100 → Level {ctx['crisis_level']} ({lv_text})\n"
        f"  Perubahan score vs bulan lalu: {ctx.get('score_delta',0):+.1f} poin | Level sebelumnya: {ctx.get('prev_level','N/A')}\n"
        f"Prediksi RF: {ctx['rf_predicted']} (confidence: {ctx['rf_confidence']}%) | "
        f"Anomali IF: {'Ya' if ctx['is_anomaly'] else 'Tidak'}\n"
        f"P(Krisis): {ctx['prob_krisis']}% | P(Siaga): {ctx['prob_siaga']}%\n"
        f"Wisman: {ctx['wisman']:,.0f} ({ctx.get('wisman_delta_pct',0):+.1f}% MoM, "
        f"trend: {ctx.get('wisman_trend','N/A')}, avg 3bln: {int(ctx.get('avg_wisman_3m',0)):,.0f})\n"
        f"TPK Hotel: {ctx['tpk_bintang']}% ({ctx.get('tpk_delta',0):+.1f}pp MoM)\n"
        f"USD/IDR: Rp {int(ctx['usd_idr']):,} ({ctx.get('usd_delta_pct',0):+.1f}% MoM)\n"
        f"Inflasi: {ctx['inflasi']}% | Sentimen: {ctx['sentiment']} ({ctx.get('sent_delta',0):+.3f} MoM)\n"
        f"Pangsa Bali: {ctx['bali_share']}% | Z-score: {ctx['wisman_zscore']}\n"
        f"Physical Risk: {ctx['physical_risk']:.1f}/100 | Media Risk: {ctx['media_risk']:.1f}/100\n"
        f"Tourist Perception: {ctx['tourist_percep']:.1f}/100 | External Risk: {ctx['external_risk']:.1f}/100\n"
        f"Histori level: {prev}\n"
        + (f"⚠️ {contradiction}\n" if contradiction else "")
    )
    return block


# ── Prompt Builders ───────────────────────────────────────────────────
def build_prompt_summary(ctx: dict) -> str:
    return (
        "Kamu adalah analis senior BaliGuard — sistem early warning pariwisata Bali.\n"
        + build_data_block(ctx)
        + f"\nTugas: Buat ringkasan analitis kondisi pariwisata Bali bulan {ctx['month']} "
        "dalam 2-3 kalimat Bahasa Indonesia yang TAJAM dan KAUSAL.\n"
        "Panduan:\n"
        "- Jelaskan MENGAPA kondisi ini terjadi, bukan hanya APA kondisinya\n"
        "- Sebutkan perubahan MoM yang paling signifikan sebagai pemicu\n"
        "- Jika ada kontradiksi antar indikator, soroti itu\n"
        "Format: cocok untuk KPI card eksekutif, padat, berbasis data."
        + NARASI_RULE
    )


def build_prompt_alert(ctx: dict) -> str:
    return (
        "Kamu adalah sistem BaliGuard. Kondisi kritis terdeteksi.\n"
        + build_data_block(ctx)
        + "\nBuat PERINGATAN DARURAT (max 130 kata) Bahasa Indonesia dengan struktur:\n"
        "STATUS: [level + score + perubahan dari bulan lalu]\n"
        "PEMICU UTAMA: [3 indikator kritis dengan perubahan MoM-nya]\n"
        "KONTEKS: [apakah ini anomali? konsisten atau tiba-tiba?]\n"
        "TINDAKAN: [1 rekomendasi segera yang spesifik dan actionable]\n"
        "Gaya: tegas, langsung, tidak bertele-tele."
        + NARASI_RULE
    )


def build_prompt_monthly(ctx: dict) -> str:
    return (
        "Kamu adalah analis senior BaliGuard.\n"
        + build_data_block(ctx)
        + "\nBuat laporan bulanan analitis Bahasa Indonesia dengan struktur berikut.\n"
        "INSTRUKSI FORMAT: Gunakan heading bold **JUDUL** untuk setiap bagian. "
        "JANGAN gunakan penomoran atau heading tanpa tanda bintang.\n\n"
        "**RINGKASAN EKSEKUTIF**\n"
        "   - Status bulan ini vs bulan lalu (naik/turun berapa poin)\n"
        "   - Apakah ini perubahan mendadak atau tren berkelanjutan?\n\n"
        "**ANALISIS INDIKATOR**\n"
        "   - Fokus pada indikator yang BERUBAH paling signifikan bulan ini\n"
        "   - Jelaskan angka dengan konteks\n"
        "   - Soroti jika ada kontradiksi antar indikator\n\n"
        "**ANALISIS KAUSAL — MENGAPA INI TERJADI?**\n"
        "   - Identifikasi kemungkinan penyebab utama, bukan sekadar deskripsi\n"
        "   - Apakah tekanan dari faktor internal atau eksternal?\n\n"
        "**REKOMENDASI PRIORITAS**\n"
        "   - 3 poin konkret dengan urgensi jelas\n"
        "   - Tiap poin: [Prioritas] Tindakan spesifik → target indikator yang diperbaiki"
        + NARASI_RULE
    )


def build_prompt_predict(ctx: dict) -> str:
    return (
        "Kamu adalah analis senior BaliGuard.\n"
        + build_data_block(ctx)
        + "\nStruktur laporan (gunakan heading bold **JUDUL**, JANGAN penomoran):\n\n"
        "**PROYEKSI KONDISI**\n"
        "   - Prediksi arah tren crisis score 3 bulan ke depan\n"
        "   - Apakah proyeksi menunjukkan pemulihan atau tekanan berlanjut?\n\n"
        "**FAKTOR RISIKO UTAMA**\n"
        "   - 3 indikator yang paling berpotensi mempengaruhi kondisi ke depan\n"
        "   - Jelaskan arah tekanan (positif/negatif) masing-masing\n\n"
        "**SKENARIO RISIKO**\n"
        "   - Skenario Optimis: kondisi terbaik yang mungkin terjadi\n"
        "   - Skenario Pesimis: kondisi terburuk jika indikator memburuk\n\n"
        "**REKOMENDASI ANTISIPATIF**\n"
        "   - Tindakan preventif yang perlu disiapkan SEKARANG\n"
        "   - Tiap poin: [Urgensi] Tindakan spesifik → dampak yang diantisipasi"
        + NARASI_RULE
    )


def build_prompt_swot(ctx: dict, format_style: str = 'paragraf') -> str:
    """
    SWOT prompt — versi lengkap sesuai narasi.py yang sudah terbukti bekerja.
    Ditambah kuadran REKOMENDASI STRATEGIS sebagai fitur baru.
    """
    return (
        "Kamu adalah analis pariwisata profesional dan penasihat strategis untuk pengambil kebijakan di Bali.\n"
        + build_data_block(ctx)
        + f"\nTugas: Buat ANALISIS SWOT pariwisata Bali bulan {ctx['month']} "
        "dalam Bahasa Indonesia yang tajam, analitis, dan memiliki penalaran mendalam (deep reasoning).\n"
        "PENTING: Langsung mulai output dengan **KEKUATAN (Strengths)**. "
        "JANGAN tambahkan judul atau header apapun sebelum bagian SWOT pertama.\n\n"

        "==================================================\n"
        "ATURAN REASONING & KLASIFIKASI (WAJIB DIPATUHI MUTLAK):\n"
        "==================================================\n"
        "1. KLASIFIKASI LEVEL RISIKO (HARGA MATI):\n"
        "   Sebelum menyimpulkan, kamu WAJIB mengklasifikasikan setiap skor indikator "
        "menggunakan skala mutlak berikut:\n"
        "   - 0 – 33   = RENDAH\n"
        "   - 34 – 66  = SEDANG\n"
        "   - 67 – 100 = TINGGI\n"
        "   DILARANG KERAS menyebut indikator sebagai 'tinggi' atau 'ancaman signifikan' "
        "hanya karena nilainya lebih besar dari indikator lain! Jika dua indikator berada "
        "pada kategori yang sama, kamu WAJIB bernarasi: '[Indikator A] lebih tinggi dibanding "
        "[Indikator B], namun kedua indikator masih berada pada kategori [kategori] "
        "sehingga ancaman terkendali'.\n\n"

        "2. IDENTIFIKASI FAKTOR DOMINAN:\n"
        "   Tentukan dan sebutkan secara eksplisit indikator dengan skor tertinggi dari seluruh "
        "data, lalu jelaskan implikasi utamanya. Pola: 'Indikator dominan pada periode ini adalah "
        "[indikator_tertinggi] ([nilai aktual]/100), yang menunjukkan bahwa...'\n\n"

        "3. LARANGAN MEMBACA DATA SECARA MEKANIS:\n"
        "   DILARANG membuat pola kalimat seperti: '[Nama indikator] [angka] menunjukkan adanya "
        "[risiko generik]'. Susun paragraf analitis yang menjelaskan hubungan sebab-akibat "
        "antar metrik.\n\n"

        "==================================================\n"
        "STRUKTUR OUTPUT SWOT (WAJIB DIIKUTI):\n"
        "==================================================\n"
        "INSTRUKSI FORMAT (HARGA MATI): Gunakan heading bold **JUDUL** untuk setiap bagian SWOT. "
        "JANGAN gunakan heading tanpa tanda bintang. JANGAN beri nomor di depan heading.\n\n"

        "**KEKUATAN (Strengths)**\n"
        "- Identifikasi faktor dominan internal atau persepsi yang paling kuat (tertinggi).\n"
        "- Jelaskan bagaimana faktor ini menjadi penyangga utama ketahanan pariwisata Bali, "
        "dan hubungkan sebab-akibatnya dengan tren data operasional (seperti tren Wisman atau TPK Hotel).\n"
        "- Maksimal 3 kalimat untuk bagian ini.\n\n"

        "**KELEMAHAN (Weaknesses)**\n"
        "- Analisis titik kerentanan internal atau penurunan performa "
        "(misal: fluktuasi Crisis Score, Inflasi, atau penurunan Sentimen).\n"
        "- Jelaskan implikasi logis dari kelemahan ini terhadap operasional pariwisata jika dibiarkan.\n"
        "- Maksimal 3 kalimat untuk bagian ini.\n\n"

        "**PELUANG (Opportunities)**\n"
        "- WAJIB BANDINGKAN: Tourist Perception vs External Risk.\n"
        f"  (Tourist Perception: {ctx['tourist_percep']:.1f}/100 | "
        f"External Risk: {ctx['external_risk']:.1f}/100)\n"
        "- Jelaskan secara analitis apakah persepsi wisatawan masih mampu menahan tekanan "
        "eksternal yang ada, atau sebaliknya. Berikan rekomendasi strategis untuk memanfaatkan "
        "momentum komparasi tersebut.\n"
        "- Maksimal 3 kalimat untuk bagian ini.\n\n"

        "**ANCAMAN (Threats)**\n"
        "- WAJIB BANDINGKAN: Physical Risk vs Media Risk. Tentukan ancaman mana yang lebih "
        "dominan memberikan tekanan reputasi/fisik saat ini.\n"
        f"  (Physical Risk: {ctx['physical_risk']:.1f}/100 | "
        f"Media Risk: {ctx['media_risk']:.1f}/100)\n"
        "- INTEGRASI KOMPREHENSIF: Masukkan Tourist Perception dan External Risk ke dalam "
        "analisis Threats ini. Apakah tekanan fisik/media saat ini sudah cukup kuat untuk "
        "menggerus kepercayaan wisatawan atau belum?\n"
        "- Jelaskan efek domino (sebab-akibat) potensial terhadap pariwisata Bali.\n"
        "- Maksimal 4 kalimat untuk bagian ini.\n\n"

        # ── FITUR BARU: Rekomendasi Strategis sebagai sintesis ──────────
        "**REKOMENDASI STRATEGIS**\n"
        "Sintesis dari seluruh SWOT di atas. JANGAN hanya mengulang isi SWOT.\n"
        "Susun narasi yang mencakup enam substansi berikut, masing-masing harus dijelaskan "
        "secara berbeda dan tidak boleh ada dua substansi yang menyampaikan ide yang sama:\n"
        "(a) tindakan dengan urgensi tertinggi berdasarkan data, "
        "(b) peluang terbesar yang harus dimanfaatkan segera, "
        "(c) ancaman yang paling perlu diantisipasi, "
        "(d) strategi jangka pendek 1–3 bulan berupa tindakan operasional konkret, "
        "(e) strategi jangka panjang 6–12 bulan berupa arah kebijakan struktural, "
        "(f) keputusan kunci untuk Dinas Pariwisata Bali.\n"
        "PENTING: jangan tulis label (a)-(f) ini secara harfiah di output — gunakan hanya sebagai "
        "checklist substansi. Cara penyajian (paragraf atau poin) WAJIB mengikuti instruksi format "
        "di akhir prompt, BUKAN format apapun yang tersirat di atas.\n"
        "Setiap substansi wajib menyebut minimal satu angka aktual dari data yang diberikan "
        "(skor, persentase, atau nilai indikator), bukan klaim generik tanpa angka.\n"
        "Gaya Bahasa keseluruhan: menulis layaknya analis ahli, bukan seperti sistem yang "
        "sedang membacakan baris data."
        + NARASI_RULE
    )

def build_prompt_comparison(ctx_a: dict, ctx_b: dict, report_type: str, format_style: str = 'paragraf') -> str:
    """
    Bangun prompt komparasi dua periode untuk semua tipe laporan.
    ctx_a = periode pertama (lebih lama), ctx_b = periode kedua (lebih baru).
    """
    return _build_prompt_comparison_inner(ctx_a, ctx_b, report_type) \
        + FORMAT_STYLE_RULE.get(format_style, FORMAT_STYLE_RULE['paragraf'])

def _build_prompt_comparison_inner(ctx_a: dict, ctx_b: dict, report_type: str) -> str:
    """
    Bangun prompt komparasi dua periode untuk semua tipe laporan.
    ctx_a = periode pertama (lebih lama), ctx_b = periode kedua (lebih baru).
    """
    block_a = build_data_block(ctx_a)
    block_b = build_data_block(ctx_b)

    base = (
        "Kamu adalah analis senior BaliGuard.\n\n"
        f"=== DATA PERIODE A: {ctx_a['month']} ===\n{block_a}\n"
        f"=== DATA PERIODE B: {ctx_b['month']} ===\n{block_b}\n\n"
    )

    if report_type == 'swot':
        return base + (
            "Tugas: Bandingkan kondisi SWOT pariwisata Bali antara dua periode di atas.\n"
            "Gunakan heading bold **JUDUL**. Tulis semua poin sebagai bullet list.\n\n"
            "**PERBANDINGAN KEKUATAN**\n"
            "- Faktor mana yang menguat dari periode A ke B?\n"
            "- Faktor mana yang melemah?\n\n"
            "**PERBANDINGAN KELEMAHAN**\n"
            "- Kelemahan baru yang muncul di periode B?\n"
            "- Kelemahan yang berhasil diatasi?\n\n"
            "**PERBANDINGAN PELUANG**\n"
            "- Peluang yang bertambah atau berkurang?\n"
            "- Perubahan Tourist Perception dan External Risk antar periode?\n\n"
            "**PERBANDINGAN ANCAMAN**\n"
            "- Ancaman yang meningkat signifikan?\n"
            "- Perubahan Physical Risk dan Media Risk antar periode?\n\n"
            "**RINGKASAN PERUBAHAN KONDISI**\n"
            f"- Crisis Score: {ctx_a['month']} ({ctx_a['crisis_score']}/100 {ctx_a['crisis_level']}) "
            f"→ {ctx_b['month']} ({ctx_b['crisis_score']}/100 {ctx_b['crisis_level']})\n"
            "- Identifikasi apakah kondisi secara keseluruhan membaik, memburuk, atau stagnan\n"
            "- Faktor paling signifikan yang mendorong perubahan ini\n\n"
            "**REKOMENDASI BERDASARKAN PERBANDINGAN**\n"
            "- Apa yang harus dipertahankan dari periode terbaik?\n"
            "- Apa yang harus diperbaiki segera berdasarkan tren?\n"
            "- Strategi adaptif berdasarkan pola dua periode ini\n"
            + NARASI_RULE
        )
    elif report_type == 'summary':
        return base + (
            "Tugas: Bandingkan kondisi pariwisata Bali antara dua periode secara ringkas.\n"
            "Gunakan heading bold **JUDUL**. Tulis poin sebagai bullet list.\n\n"
            "**PERBANDINGAN KONDISI UTAMA**\n"
            f"- Crisis Score: {ctx_a['month']} {ctx_a['crisis_score']}/100 vs {ctx_b['month']} {ctx_b['crisis_score']}/100\n"
            "- Indikator yang paling banyak berubah antar periode\n"
            "- Arah perubahan: membaik atau memburuk?\n\n"
            "**FAKTOR PERUBAHAN**\n"
            "- Penyebab utama perbedaan kondisi dua periode\n"
            "- Indikator mana yang konsisten vs yang fluktuatif\n\n"
            "**KESIMPULAN RINGKAS**\n"
            "- 1–2 kalimat: apa yang paling penting dari perbandingan ini?"
            + NARASI_RULE
        )
    elif report_type == 'alert':
        return base + (
            "Tugas: Bandingkan kondisi kritis antara dua periode.\n"
            "Gunakan heading bold **JUDUL**.\n\n"
            "**PERBANDINGAN STATUS**\n"
            f"- Periode A ({ctx_a['month']}): Level {ctx_a['crisis_level']}, Score {ctx_a['crisis_score']}/100\n"
            f"- Periode B ({ctx_b['month']}): Level {ctx_b['crisis_level']}, Score {ctx_b['crisis_score']}/100\n"
            "- Apakah kondisi membaik atau memburuk?\n\n"
            "**PERUBAHAN INDIKATOR KRITIS**\n"
            "- 3 indikator yang perubahannya paling signifikan antar periode\n"
            "- Arah perubahan masing-masing (membaik/memburuk)\n\n"
            "**TINDAKAN BERDASARKAN PERBANDINGAN**\n"
            "- Jika memburuk: tindakan korektif yang diperlukan\n"
            "- Jika membaik: tindakan preventif untuk mempertahankan"
            + NARASI_RULE
        )
    elif report_type == 'monthly':
        return base + (
            "Tugas: Buat laporan komparatif bulanan antara dua periode.\n"
            "Gunakan heading bold **JUDUL**.\n\n"
            "**RINGKASAN EKSEKUTIF KOMPARATIF**\n"
            "- Gambaran perubahan kondisi dari periode A ke B\n"
            "- Apakah tren ini mengkhawatirkan atau menjanjikan?\n\n"
            "**ANALISIS INDIKATOR KOMPARATIF**\n"
            "- Indikator yang membaik signifikan\n"
            "- Indikator yang memburuk signifikan\n"
            "- Indikator yang stagnan\n\n"
            "**ANALISIS KAUSAL**\n"
            "- Mengapa terjadi perubahan tersebut?\n"
            "- Faktor internal vs eksternal yang mendominasi\n\n"
            "**REKOMENDASI ADAPTIF**\n"
            "- 3 poin rekomendasi berdasarkan tren dua periode ini"
            + NARASI_RULE
        )
    else:  # predict
        return base + (
            "Tugas: Buat proyeksi komparatif berdasarkan dua periode data.\n"
            "Gunakan heading bold **JUDUL**.\n\n"
            "**PERUBAHAN TREN**\n"
            "- Arah tren dari periode A ke B\n"
            "- Apakah momentum menunjukkan perbaikan atau pelemahan?\n\n"
            "**PROYEKSI BERDASARKAN DUA PERIODE**\n"
            "- Skenario Optimis berdasarkan tren terbaik dua periode\n"
            "- Skenario Pesimis jika tren negatif berlanjut\n\n"
            "**REKOMENDASI ANTISIPATIF**\n"
            "- Tindakan preventif berdasarkan pola dua periode"
            + NARASI_RULE
        )


def build_prompt(ctx: dict, report_type: str, format_style: str = 'paragraf') -> str:
    """Router utama: pilih prompt builder berdasarkan report_type."""
    if report_type == 'swot':
        base_prompt = build_prompt_swot(ctx, format_style)
    else:
        builders = {
            'summary': build_prompt_summary,
            'alert':   build_prompt_alert,
            'monthly': build_prompt_monthly,
            'predict': build_prompt_predict,
        }
        fn = builders.get(report_type, build_prompt_summary)
        base_prompt = fn(ctx)
    return base_prompt + FORMAT_STYLE_RULE.get(format_style, FORMAT_STYLE_RULE['paragraf'])


# ── Context Builder ───────────────────────────────────────────────────
def build_ctx(row_data: dict, history: list) -> dict:
    """
    Bangun ctx dict dari satu baris predictions dan history rows.
    Dipanggil dari narasi.py — menghilangkan logika inline di sana.
    """
    import numpy as np

    ctx = {
        'month':          str(row_data.get('month', 'N/A')),
        'crisis_score':   round(float(row_data.get('crisis_score_100', 0)), 1),
        'crisis_level':   str(row_data.get('crisis_level', 'WASPADA')),
        'rf_predicted':   str(row_data.get('rf_predicted_level', 'N/A')),
        'rf_confidence':  round(float(row_data.get('rf_confidence', 0)) * 100, 1),
        'is_anomaly':     int(float(row_data.get('iso_anomaly', 0))),
        'wisman':         int(float(row_data.get('wisman', 0))),
        'tpk_bintang':    round(float(row_data.get('tpk_bintang', 0)), 1),
        'inflasi':        round(float(row_data.get('inflasi_processed', 0)), 2),
        'usd_idr':        round(float(row_data.get('usd_idr_avg', 0)), 0),
        'sentiment':      round(float(row_data.get('avg_sentiment_monthly', 0)), 3),
        'prob_krisis':    round(float(row_data.get('prob_krisis', 0)) * 100, 1),
        'prob_siaga':     round(float(row_data.get('prob_siaga', 0)) * 100, 1),
        'bali_share':     round(float(row_data.get('bali_share_pct', 0)), 1),
        'wisman_zscore':  round(float(row_data.get('wisman_zscore', 0)), 2),
        'physical_risk':  round(float(row_data.get('physical_risk_score', 0)) * 100, 1),
        'media_risk':     round(float(row_data.get('media_risk_score', 0)) * 100, 1),
        'tourist_percep': round(float(row_data.get('tourist_perception_score', 0)) * 100, 1),
        'external_risk':  round(float(row_data.get('external_risk_score', 0)) * 100, 1),
    }

    if history:
        avg3 = np.mean([r.get('wisman', 0) for r in history[-3:]])
        prev = history[-1]
        prev_w = float(prev.get('wisman', 1))
        ctx.update({
            'wisman_trend':     'naik' if ctx['wisman'] > avg3 else 'turun',
            'avg_wisman_3m':    round(avg3, 0),
            'prev_levels':      [r.get('crisis_level', 'N/A') for r in history[-3:]],
            'prev_level':       prev.get('crisis_level', 'N/A'),
            'wisman_delta_pct': round((ctx['wisman'] - prev_w) / max(1, prev_w) * 100, 1),
            'score_delta':      round(ctx['crisis_score'] - float(prev.get('crisis_score_100', ctx['crisis_score'])), 1),
            'sent_delta':       round(ctx['sentiment'] - float(prev.get('avg_sentiment_monthly', ctx['sentiment'])), 3),
            'tpk_delta':        round(ctx['tpk_bintang'] - float(prev.get('tpk_bintang', ctx['tpk_bintang'])), 1),
            'usd_delta_pct':    round((float(prev.get('usd_idr_avg', 0)) and
                                (ctx['usd_idr'] - float(prev.get('usd_idr_avg', 0))) /
                                float(prev.get('usd_idr_avg', 1)) * 100) or 0, 1),
        })
    else:
        ctx.update({
            'wisman_trend': 'tidak tersedia', 'avg_wisman_3m': 0,
            'prev_levels': [], 'prev_level': 'N/A',
            'wisman_delta_pct': 0, 'score_delta': 0,
            'sent_delta': 0, 'tpk_delta': 0, 'usd_delta_pct': 0,
        })
    return ctx

# ── Post-processor ────────────────────────────────────────────────────
def clean_output(text: str) -> str:
    """Hapus karakter non-Latin yang bocor dari output LLM."""
    for cjk, replacement in CJK_FIXES.items():
        text = text.replace(cjk, replacement)
    if NON_LATIN_PATTERN.search(text):
        text = NON_LATIN_PATTERN.sub('', text)
        text = re.sub(r' {2,}', ' ', text).strip()
    return text


