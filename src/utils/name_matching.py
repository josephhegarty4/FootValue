from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd
from rapidfuzz import fuzz, process


_CHAR_REPLACEMENTS = str.maketrans(
    {
        "ø": "o",
        "Ø": "O",
        "đ": "d",
        "Đ": "D",
        "ł": "l",
        "Ł": "L",
        "ß": "ss",
        "æ": "ae",
        "Æ": "AE",
        "œ": "oe",
        "Œ": "OE",
    }
)


@dataclass
class MatchResult:
    source_name: str
    matched_name: Optional[str]
    score: float
    method: str


def normalize_name(name: str) -> str:
    cleaned = str(name).translate(_CHAR_REPLACEMENTS)
    cleaned = unicodedata.normalize("NFKD", cleaned).encode("ascii", "ignore").decode("ascii")
    cleaned = cleaned.lower().strip()
    cleaned = re.sub(r"[^a-z\s'-]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def load_manual_corrections(path: str | Path) -> Dict[str, str]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return {normalize_name(key): value for key, value in data.items()}


def save_manual_corrections(path: str | Path, corrections: Dict[str, str]) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as file:
        json.dump(dict(sorted(corrections.items())), file, indent=2, ensure_ascii=False)


def build_name_mapping(
    source_names: Iterable[str],
    target_names: Iterable[str],
    manual_corrections: Optional[Dict[str, str]] = None,
    score_cutoff: float = 88.0,
) -> Dict[str, MatchResult]:
    manual_corrections = manual_corrections or {}
    target_name_list = list(target_names)
    normalized_target_lookup = {normalize_name(name): name for name in target_name_list}

    mapping: Dict[str, MatchResult] = {}

    for source_name in source_names:
        normalized_source = normalize_name(source_name)

        if normalized_source in manual_corrections:
            corrected_target = manual_corrections[normalized_source]
            mapping[source_name] = MatchResult(
                source_name=source_name,
                matched_name=corrected_target,
                score=100.0,
                method="manual",
            )
            continue

        if normalized_source in normalized_target_lookup:
            mapping[source_name] = MatchResult(
                source_name=source_name,
                matched_name=normalized_target_lookup[normalized_source],
                score=100.0,
                method="exact-normalized",
            )
            continue

        best_match = process.extractOne(
            source_name,
            target_name_list,
            scorer=fuzz.WRatio,
            score_cutoff=score_cutoff,
        )

        if best_match is None:
            mapping[source_name] = MatchResult(
                source_name=source_name,
                matched_name=None,
                score=0.0,
                method="unmatched",
            )
            continue

        matched_name, score, _ = best_match
        mapping[source_name] = MatchResult(
            source_name=source_name,
            matched_name=matched_name,
            score=float(score),
            method="fuzzy",
        )

    return mapping


def fuzzy_join(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_name_col: str,
    right_name_col: str,
    manual_corrections_path: str | Path,
    score_cutoff: float = 88.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    corrections = load_manual_corrections(manual_corrections_path)
    mapping = build_name_mapping(
        source_names=left_df[left_name_col].dropna().astype(str).unique(),
        target_names=right_df[right_name_col].dropna().astype(str).unique(),
        manual_corrections=corrections,
        score_cutoff=score_cutoff,
    )

    mapping_df = pd.DataFrame(
        [
            {
                "source_name": result.source_name,
                "matched_name": result.matched_name,
                "match_score": result.score,
                "match_method": result.method,
            }
            for result in mapping.values()
        ]
    )

    merged = (
        left_df.merge(mapping_df, left_on=left_name_col, right_on="source_name", how="left")
        .merge(right_df, left_on="matched_name", right_on=right_name_col, how="left", suffixes=("", "_tm"))
        .drop(columns=["source_name"], errors="ignore")
    )

    unmatched = mapping_df[mapping_df["matched_name"].isna()].copy()
    return merged, unmatched
