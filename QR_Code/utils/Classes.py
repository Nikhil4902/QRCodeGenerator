from __future__ import annotations

from enum import Enum
from strenum import StrEnum  # StrEnum was added to enum in 3.11


class Regex(StrEnum):
    NUMERIC = r"^[0-9]*$"
    ALPHA_NUMERIC = r"^[0-9A-Z $%*+-./:]*$"
    BYTE = r"^[\u0000-\u00ff]*$"
    KANJI = r"(?!x)x"  # don't know the regex so using a regex that never matches with anything


class EncodingMode(Enum):
    """Encoding mode for the encoder."""

    NUMERIC = 0b0001  # 1
    ALPHA_NUMERIC = 0b0010  # 2
    BYTE = 0b0100  # 4
    KANJI = 0b1000  # 8
    ECI = 0b0111  # 7


class ECCode(Enum):
    L = 1
    M = 0
    Q = 3
    H = 2
