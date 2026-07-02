"""
automation/process/common_checks.py — BaliGuard Automation: Generic Validators

Validasi generik yang dipakai LINTAS SOURCE. Tidak ada logic spesifik
USD/Trends/GDELT/dsb di sini — itu ada di process/validate_<source>.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.is_valid = False
        self.errors.append(msg)


def check_month_format(month: str, result: ValidationResult) -> None:
    if not isinstance(month, str) or not re.match(r"^\d{4}-\d{2}$", month):
        result.add_error(f"month '{month}' tidak berformat YYYY-MM")


def check_not_null(value, field_name: str, result: ValidationResult) -> None:
    if value is None:
        result.add_error(f"field '{field_name}' wajib tidak null")


def check_numeric_range(value: float, field_name: str, min_v: float, max_v: float,
                         result: ValidationResult) -> None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        result.add_error(f"field '{field_name}' bukan angka valid: {value!r}")
        return
    if v != v:  # NaN check tanpa import numpy
        result.add_error(f"field '{field_name}' bernilai NaN")
        return
    if not (min_v <= v <= max_v):
        result.add_error(
            f"field '{field_name}'={v} di luar rentang masuk akal [{min_v}, {max_v}]"
        )
