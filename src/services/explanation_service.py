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

# Risk score ditampilkan sebagai nilai mentah.
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

# ── Indikator "Kondisi Risiko Saat Ini" — semua sudah 0-100 dari pipeline ──
_RISK_SCORE_KEYS = [
    ("media_risk", "Media Risk"),
    ("physical_risk", "Physical Risk"),
    ("tourist_perception", "Tourist Perception"),
    ("external_risk", "External Risk"),
]

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
        if pct == 0:
            continue
        arah = "naik" if pct > 0 else "turun"
        perubahan.append(f"{name} {arah} {abs(pct):.1f}%")

    d_sent = delta_ctx.get("avg_sentiment_monthly")
    if d_sent:
        delta = sf(d_sent.get("delta"))
        if delta != 0:
            arah = "menguat" if delta > 0 else "melemah"
            perubahan.append(f"Sentimen {arah} {abs(delta):.2f} poin")

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
        val = sf(val)
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
