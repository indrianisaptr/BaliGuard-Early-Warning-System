"""
src/services/explanation_service.py — BaliGuard: Explanation Panel Logic
==========================================================================
Business logic murni untuk panel "Mengapa Status Ini Muncul?" di
src/pages/overview.py.

TIDAK ADA di file ini:
- Streamlit (st.*)
- HTML/CSS
- Perhitungan ulang pipeline, Random Forest, Crisis Score
- Threshold/severity/ranking baru

Semua angka yang dipakai berasal 100% dari ctx (hasil src.shared.build_context()).
File ini hanya MENYUSUN teks penjelasan dari angka yang sudah dihitung tempat lain.

# Risk score ditampilkan sebagai nilai mentah, dinormalisasi ke skala 0-100
# (lihat _normalize_risk_scale) supaya konsisten dengan kartu "External Risk
# Monitor" di overview.py — keduanya membaca field ctx yang sama, yang
# ternyata berskala 0-1 di pipeline saat ini, bukan 0-100.
# Kategorisasi level tidak dilakukan di sini karena interpretasinya
# merupakan tanggung jawab pipeline jika tersedia.
"""

from src.utils import sf


# ── Indikator "Perubahan Utama" — semua berbasis delta_ctx ────────────
_PERUBAHAN_PERSEN_KEYS = [
    ("wisman", "Wisatawan"),
    ("usd_idr_avg", "Kurs USD/IDR"),
    ("tpk_bintang", "TPK"),
    ("bali_share_pct", "Pangsa Wisatawan Bali"),
]

# ── Indikator "Kondisi Risiko Saat Ini" ────────────────────────────────
_RISK_SCORE_KEYS = [
    ("media_risk", "Media Risk"),
    ("physical_risk", "Physical Risk"),
    ("tourist_perception", "Tourist Perception"),
    ("external_risk", "External Risk"),
]


def _normalize_risk_scale(val: float) -> float:
    """
    Normalisasi skala risk score ke 0-100.

    Field risk (media_risk, physical_risk, tourist_perception, external_risk)
    ternyata TIDAK selalu berskala 0-100 seperti asumsi komentar di atas —
    di ctx (lihat src/shared.py) nilainya diteruskan mentah dari
    row_data.get('*_risk_score', 0) tanpa transformasi. Kartu "External Risk
    Monitor" di overview.py sudah menyadari ini dan menormalisasi sendiri
    lewat _risk_pct(): val*100 kalau val<=1 (skala 0-1), dipakai apa adanya
    kalau val>1 (sudah 0-100). Logika di sini SENGAJA dibuat identik supaya
    panel ini dan kartu tersebut selalu menampilkan angka yang konsisten
    untuk field yang sama, apa pun skala asli yang dikirim pipeline.
    """
    return val * 100 if val <= 1 else val

MESSAGES = {
    "no_change": "Tidak terdapat perubahan berarti pada indikator pariwisata dibanding bulan sebelumnya",
    "no_risk_data": "Data kondisi risiko tidak tersedia untuk bulan ini",
    "summary_template": (
        "Secara keseluruhan, perubahan indikator pariwisata dan kondisi risiko "
        "pada bulan ini tercermin pada Crisis Score sebesar {score:.1f} "
        "sehingga status berada pada level {level}."
    ),
}


def _build_perubahan(ctx: dict) -> list[str]:
    """Susun daftar perubahan yang benar-benar terjadi (delta_pct != 0 / delta != 0)."""
    delta_ctx = ctx.get("delta_ctx", {}) or {}
    perubahan: list[str] = []

    for key, name in _PERUBAHAN_PERSEN_KEYS:
        d = delta_ctx.get(key)
        if not d:
            continue
        pct = sf(d.get("delta_pct"))
        pct_rounded = round(pct, 1)
        # Bandingkan nilai yang SUDAH dibulatkan (bukan nilai mentah), supaya
        # konsisten dengan tampilan `.1f` di bawah. Tanpa ini, delta kecil
        # (mis. 0.04%) lolos filter "!= 0" tapi dibulatkan jadi tampak
        # "naik/turun 0.0%" — kalimat yang aneh dan tidak informatif.
        if pct_rounded == 0:
            continue
        arah = "naik" if pct_rounded > 0 else "turun"
        perubahan.append(f"{name} {arah} {abs(pct_rounded):.1f}%")

    d_sent = delta_ctx.get("avg_sentiment_monthly")
    if d_sent:
        delta = sf(d_sent.get("delta"))
        delta_rounded = round(delta, 2)
        if delta_rounded != 0:
            arah = "menguat" if delta_rounded > 0 else "melemah"
            perubahan.append(f"Sentimen {arah} {abs(delta_rounded):.2f} poin")

    if not perubahan:
        perubahan = [MESSAGES["no_change"]]

    return perubahan


def _build_risiko(ctx: dict) -> list[str]:
    """Susun daftar kondisi risiko sebagai angka mentah, tanpa kategori."""
    risiko: list[str] = []

    for key, name in _RISK_SCORE_KEYS:
        val = ctx.get(key)
        if val is None:
            continue
        val = _normalize_risk_scale(sf(val))
        risiko.append(f"{name} berada pada {val:.1f}/100")

    if not risiko:
        risiko = [MESSAGES["no_risk_data"]]

    return risiko


def _build_summary(ctx: dict) -> str:
    """
    Kesimpulan netral — bukan klaim kausal. Menggunakan 'tercermin pada',
    bukan 'menyebabkan'/'akibat'/'dipicu'/'karena', karena kita hanya
    menunjukkan evidence yang berkorelasi, bukan hubungan sebab-akibat
    yang benar-benar dihitung/diuji.
    """
    score = sf(ctx["score"])
    level = ctx.get("level", "N/A")
    return MESSAGES["summary_template"].format(score=score, level=level)


def build_explanation_context(ctx: dict) -> dict:
    """
    Titik masuk utama. Dipanggil dari overview.py.

    Catatan: fungsi ini hanya menerima `ctx` karena seluruh data yang
    dibutuhkan (delta_ctx, media_risk, physical_risk, tourist_perception,
    external_risk, score, level) sudah tersedia di dalamnya lewat
    src.shared.build_context(). row_data sengaja TIDAK dijadikan parameter
    agar signature fungsi jujur — tidak ada parameter yang tidak dipakai.

    Return:
        {
            "perubahan": [str, ...],
            "risiko": [str, ...],
            "summary": str,
        }
    """
    return {
        "perubahan": _build_perubahan(ctx),
        "risiko": _build_risiko(ctx),
        "summary": _build_summary(ctx),
    }
