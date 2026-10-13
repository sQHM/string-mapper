"""
String Matcher - Direct and fuzzy matching logic.
Handles Chinese characters and numbers effectively.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

from .chinese_handler import ChineseTextHandler


class MatchType(Enum):
    """Type of match found."""
    EXACT = "exact"
    DIRECT = "direct"
    FUZZY = "fuzzy"
    NO_MATCH = "no_match"


@dataclass
class MatchResult:
    """Result of a single match operation."""
    source_value: str
    matched_value: Optional[str]
    match_type: MatchType
    score: float
    source_df_name: str
    matched_row_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        return {
            "source_value": self.source_value,
            "matched_value": self.matched_value,
            "match_type": self.match_type.value,
            "score": self.score,
            "source_df_name": self.source_df_name,
            "matched_row_data": self.matched_row_data,
        }


class StringMatcher:
    """
    Main matching engine for string comparison.
    Supports direct matching and fuzzy matching with Chinese text support.
    """

    def __init__(self, fuzzy_threshold: float = 70.0):
        """
        Initialize the matcher.

        Args:
            fuzzy_threshold: Minimum score (0-100) for fuzzy match acceptance
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.text_handler = ChineseTextHandler()

    def _prepare_value(self, value: Any) -> str:
        """Convert value to string and normalize."""
        if pd.isna(value):
            return ""
        return self.text_handler.prepare_for_matching(str(value))

    def _calculate_score(self, s1: str, s2: str) -> float:
        """
        Calculate similarity score between two strings.
        Uses multiple methods and returns the best score.
        """
        if not s1 or not s2:
            return 0.0

        scores = [
            fuzz.ratio(s1, s2),
            fuzz.partial_ratio(s1, s2),
            fuzz.token_sort_ratio(s1, s2),
            fuzz.token_set_ratio(s1, s2),
        ]

        if self.text_handler.contains_chinese(s1) or self.text_handler.contains_chinese(s2):
            tokens1 = self.text_handler.tokenize(s1)
            tokens2 = self.text_handler.tokenize(s2)

            if tokens1 and tokens2:
                common = set(tokens1) & set(tokens2)
                token_score = (len(common) / max(len(set(tokens1)), len(set(tokens2)))) * 100
                scores.append(token_score)

        nums1 = self.text_handler.extract_numbers(s1)
        nums2 = self.text_handler.extract_numbers(s2)
        if nums1 and nums2:
            num_match = len(set(nums1) & set(nums2)) / max(len(set(nums1)), len(set(nums2)))
            scores.append(num_match * 100)

        return max(scores)

    def direct_match(
        self,
        target_value: str,
        candidates: List[str],
        case_sensitive: bool = False
    ) -> Optional[Tuple[str, int]]:
        """
        Perform direct (exact) matching.

        Returns:
            Tuple of (matched_value, index) or None if no match
        """
        prepared_target = self._prepare_value(target_value)
        if not prepared_target:
            return None

        for idx, candidate in enumerate(candidates):
            prepared_candidate = self._prepare_value(candidate)
            if not prepared_candidate:
                continue

            if case_sensitive:
                if str(target_value).strip() == str(candidate).strip():
                    return (candidate, idx)
            else:
                if prepared_target == prepared_candidate:
                    return (candidate, idx)

        return None

    def fuzzy_match(
        self,
        target_value: str,
        candidates: List[str],
        limit: int = 3
    ) -> List[Tuple[str, float, int]]:
        """
        Perform fuzzy matching using multiple algorithms.

        Returns:
            List of (matched_value, score, index) sorted by score descending
        """
        prepared_target = self._prepare_value(target_value)
        if not prepared_target:
            return []

        prepared_candidates = [(self._prepare_value(c), i, c) for i, c in enumerate(candidates)]
        prepared_candidates = [(p, i, orig) for p, i, orig in prepared_candidates if p]

        if not prepared_candidates:
            return []

        results = []
        for prepared, idx, original in prepared_candidates:
            score = self._calculate_score(prepared_target, prepared)
            if score >= self.fuzzy_threshold:
                results.append((original, score, idx))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def match_single(
        self,
        target_value: str,
        df: pd.DataFrame,
        match_column: str,
        df_name: str = "unnamed"
    ) -> MatchResult:
        """
        Match a single target value against a DataFrame column.

        Returns:
            MatchResult with match details
        """
        candidates = df[match_column].astype(str).tolist()

        direct_result = self.direct_match(target_value, candidates)
        if direct_result:
            matched_value, idx = direct_result
            matched_row = df.iloc[idx].to_dict()

            prepared_target = self._prepare_value(target_value)
            prepared_match = self._prepare_value(matched_value)
            is_exact = str(target_value).strip() == str(matched_value).strip()

            return MatchResult(
                source_value=target_value,
                matched_value=matched_value,
                match_type=MatchType.EXACT if is_exact else MatchType.DIRECT,
                score=100.0,
                source_df_name=df_name,
                matched_row_data=matched_row,
            )

        fuzzy_results = self.fuzzy_match(target_value, candidates, limit=1)
        if fuzzy_results:
            matched_value, score, idx = fuzzy_results[0]
            matched_row = df.iloc[idx].to_dict()

            return MatchResult(
                source_value=target_value,
                matched_value=matched_value,
                match_type=MatchType.FUZZY,
                score=score,
                source_df_name=df_name,
                matched_row_data=matched_row,
            )

        return MatchResult(
            source_value=target_value,
            matched_value=None,
            match_type=MatchType.NO_MATCH,
            score=0.0,
            source_df_name=df_name,
            matched_row_data=None,
        )

    def match_dataframes(
        self,
        source_df: pd.DataFrame,
        target_column: str,
        info_columns: List[str],
        lookup_dfs: List[Tuple[pd.DataFrame, str, str]],
    ) -> pd.DataFrame:
        """
        Match source DataFrame against multiple lookup DataFrames.

        Args:
            source_df: Source DataFrame with target values
            target_column: Column in source_df to match
            info_columns: Additional columns to include in results
            lookup_dfs: List of (DataFrame, match_column, df_name) tuples

        Returns:
            DataFrame with match results
        """
        results = []

        for idx, row in source_df.iterrows():
            target_value = row[target_column]
            row_result = {
                "row_index": idx,
                target_column: target_value,
            }

            for col in info_columns:
                if col in row:
                    row_result[col] = row[col]

            best_match: Optional[MatchResult] = None

            for df, match_col, df_name in lookup_dfs:
                match_result = self.match_single(target_value, df, match_col, df_name)

                if match_result.match_type != MatchType.NO_MATCH:
                    if best_match is None or match_result.score > best_match.score:
                        best_match = match_result

            if best_match and best_match.match_type != MatchType.NO_MATCH:
                row_result["matched_value"] = best_match.matched_value
                row_result["match_type"] = best_match.match_type.value
                row_result["match_score"] = best_match.score
                row_result["matched_from"] = best_match.source_df_name

                if best_match.matched_row_data:
                    for key, value in best_match.matched_row_data.items():
                        row_result[f"lookup_{key}"] = value
            else:
                row_result["matched_value"] = None
                row_result["match_type"] = MatchType.NO_MATCH.value
                row_result["match_score"] = 0.0
                row_result["matched_from"] = None

            results.append(row_result)

        return pd.DataFrame(results)

    def get_all_matches(
        self,
        target_value: str,
        df: pd.DataFrame,
        match_column: str,
        df_name: str = "unnamed",
        limit: int = 5
    ) -> List[MatchResult]:
        """
        Get all potential matches for a target value (for review).

        Returns:
            List of MatchResult objects sorted by score
        """
        candidates = df[match_column].astype(str).tolist()
        results = []

        direct_result = self.direct_match(target_value, candidates)
        if direct_result:
            matched_value, idx = direct_result
            matched_row = df.iloc[idx].to_dict()
            is_exact = str(target_value).strip() == str(matched_value).strip()

            results.append(MatchResult(
                source_value=target_value,
                matched_value=matched_value,
                match_type=MatchType.EXACT if is_exact else MatchType.DIRECT,
                score=100.0,
                source_df_name=df_name,
                matched_row_data=matched_row,
            ))

        fuzzy_results = self.fuzzy_match(target_value, candidates, limit=limit)
        for matched_value, score, idx in fuzzy_results:
            if direct_result and idx == direct_result[1]:
                continue

            matched_row = df.iloc[idx].to_dict()
            results.append(MatchResult(
                source_value=target_value,
                matched_value=matched_value,
                match_type=MatchType.FUZZY,
                score=score,
                source_df_name=df_name,
                matched_row_data=matched_row,
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
