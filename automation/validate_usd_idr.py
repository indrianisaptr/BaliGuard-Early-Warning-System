"""
automation/process/validate_usd_idr.py — BaliGuard Automation: USD/IDR Validator

Validasi (range, null, format) + cleaning ringan untuk hasil fetch USD/IDR.
TIDAK melakukan feature engineering apa pun — itu domain pipeline ML (NB01-NB04),
tidak disentuh di sini.
"""
from __future__ import annotations

from automation.process.common_checks import (
    ValidationResult,
    check_month_format,
    check_not_null,
    check_numeric_range,
)

USD_IDR_MIN = 5000
USD_IDR_MAX = 30000


def validate_usd_record(record: dict) -> ValidationResult:
    """
    Input: record mentah hasil fetch/usd_idr.py, bentuk:
        {'month': 'YYYY-MM', 'usd_idr_avg': float, 'usd_idr_source': str, 'fetched_at': str}
    Output: ValidationResult(is_valid, errors)
    """
    result = ValidationResult(is_valid=True)

    check_month_format(record.get("month"), result)
    check_not_null(record.get("usd_idr_avg"), "usd_idr_avg", result)

    if record.get("usd_idr_avg") is not None:
        check_numeric_range(
            record["usd_idr_avg"], "usd_idr_avg", USD_IDR_MIN, USD_IDR_MAX, result
        )

    if not record.get("usd_idr_source"):
        result.add_error("usd_idr_source wajib diisi (jejak audit asal data)")

    if not record.get("fetched_at"):
        result.add_error("fetched_at wajib diisi (jejak audit waktu fetch)")

    return result


def clean_usd_record(record: dict) -> dict:
    """
    Cleaning RINGAN saja sesuai scope automation:
    - month dipastikan string trim
    - usd_idr_avg dibulatkan 4 desimal (presisi kurs wajar, hindari noise float)
    Tidak melakukan agregasi/feature engineering apa pun.
    """
    cleaned = dict(record)
    if cleaned.get("month"):
        cleaned["month"] = str(cleaned["month"]).strip()
    if cleaned.get("usd_idr_avg") is not None:
        cleaned["usd_idr_avg"] = round(float(cleaned["usd_idr_avg"]), 4)
    return cleaned
