from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


@dataclass(frozen=True)
class InflationIndex:
    base_year: int
    index_by_year: Dict[int, float]

    def factor(self, from_year: int, to_year: int | None = None) -> float:
        target_year = self.base_year if to_year is None else to_year
        if from_year not in self.index_by_year:
            raise KeyError(f"Missing inflation index for from_year={from_year}")
        if target_year not in self.index_by_year:
            raise KeyError(f"Missing inflation index for to_year={target_year}")
        return self.index_by_year[target_year] / self.index_by_year[from_year]


def build_index_from_series(year_to_value: Dict[int, float], base_year: int | None = None) -> InflationIndex:
    if not year_to_value:
        raise ValueError("year_to_value cannot be empty")
    chosen_base_year = max(year_to_value) if base_year is None else base_year
    if chosen_base_year not in year_to_value:
        raise KeyError(f"base_year={chosen_base_year} not present in index data")
    return InflationIndex(base_year=chosen_base_year, index_by_year=dict(year_to_value))


def normalize_fee(amount: float, from_year: int, index: InflationIndex, to_year: int | None = None) -> float:
    return amount * index.factor(from_year=from_year, to_year=to_year)


def denormalize_fee(amount: float, to_year: int, index: InflationIndex, from_year: int | None = None) -> float:
    source_year = index.base_year if from_year is None else from_year
    return amount / index.factor(from_year=to_year, to_year=source_year)


def build_linear_proxy_index(years: Iterable[int], anchor_year: int, annual_rate: float = 0.03) -> InflationIndex:
    sorted_years = sorted(set(years))
    if not sorted_years:
        raise ValueError("years cannot be empty")
    index = {year: (1 + annual_rate) ** (year - anchor_year) for year in sorted_years}
    return InflationIndex(base_year=anchor_year, index_by_year=index)
