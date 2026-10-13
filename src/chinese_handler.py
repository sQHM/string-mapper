"""
Chinese Text Handler - Preprocessing for Chinese and mixed-language strings.
Handles Chinese characters, numbers, and mixed content effectively.
"""

import re
import unicodedata
from typing import List, Optional

import jieba


class ChineseTextHandler:
    """Handler for Chinese text preprocessing and normalization."""

    def __init__(self):
        jieba.setLogLevel(jieba.logging.INFO)
        jieba.initialize()

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text by:
        - Converting to lowercase
        - Normalizing Unicode (NFKC for Chinese compatibility)
        - Normalizing whitespace
        - Converting full-width characters to half-width
        """
        if not text or not isinstance(text, str):
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = text.lower()
        text = ChineseTextHandler._fullwidth_to_halfwidth(text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @staticmethod
    def _fullwidth_to_halfwidth(text: str) -> str:
        """Convert full-width characters to half-width."""
        result = []
        for char in text:
            code = ord(char)
            if 0xFF01 <= code <= 0xFF5E:
                result.append(chr(code - 0xFEE0))
            elif code == 0x3000:
                result.append(" ")
            else:
                result.append(char)
        return "".join(result)

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """Extract all numbers (including Chinese numbers) from text."""
        chinese_num_map = {
            "零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9",
            "十": "10", "百": "100", "千": "1000", "万": "10000",
            "〇": "0", "壹": "1", "贰": "2", "叁": "3", "肆": "4",
            "伍": "5", "陆": "6", "柒": "7", "捌": "8", "玖": "9",
        }

        normalized = ChineseTextHandler.normalize_text(text)
        for cn, num in chinese_num_map.items():
            normalized = normalized.replace(cn, num)

        numbers = re.findall(r"\d+\.?\d*", normalized)
        return numbers

    @staticmethod
    def is_chinese_char(char: str) -> bool:
        """Check if a character is Chinese."""
        if len(char) != 1:
            return False
        code = ord(char)
        return (
            0x4E00 <= code <= 0x9FFF or
            0x3400 <= code <= 0x4DBF or
            0x20000 <= code <= 0x2A6DF or
            0x2A700 <= code <= 0x2B73F or
            0x2B740 <= code <= 0x2B81F or
            0xF900 <= code <= 0xFAFF or
            0x2F800 <= code <= 0x2FA1F
        )

    @staticmethod
    def contains_chinese(text: str) -> bool:
        """Check if text contains any Chinese characters."""
        return any(ChineseTextHandler.is_chinese_char(c) for c in text)

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text using jieba for Chinese and simple splitting for others.
        Returns list of tokens.
        """
        if not text:
            return []

        normalized = self.normalize_text(text)

        if self.contains_chinese(normalized):
            tokens = list(jieba.cut(normalized, cut_all=False))
        else:
            tokens = normalized.split()

        return [t.strip() for t in tokens if t.strip()]

    def prepare_for_matching(self, text: str) -> str:
        """
        Prepare text for matching by normalizing and optionally tokenizing.
        Returns a clean string ready for comparison.
        """
        if not text or not isinstance(text, str):
            return ""

        normalized = self.normalize_text(text)
        return normalized

    def get_text_components(self, text: str) -> dict:
        """
        Extract different components from text for matching.
        Returns dict with: normalized, tokens, numbers, has_chinese
        """
        normalized = self.normalize_text(text)
        return {
            "normalized": normalized,
            "tokens": self.tokenize(text),
            "numbers": self.extract_numbers(text),
            "has_chinese": self.contains_chinese(text),
        }
