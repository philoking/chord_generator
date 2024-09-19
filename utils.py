import re
from enum import Enum, auto

class ChordType(Enum):
    ROMAN = auto()
    CHORD_SYMBOL = auto()
    INVALID = auto()

# Precompile regex patterns
ROMAN_PATTERN = re.compile(r'^(IV|I{1,3}|VI{0,3}|iv|i{1,3}|vi{0,3})°?')
ROOT_PATTERN = re.compile(r'([A-G][b#]?)')
QUALITY_PATTERN = re.compile(r'(maj|min|m|M|\+|aug|dim)?')
EXTENSIONS_PATTERN = re.compile(r'((?:maj|add|sus|[0-9])*[0-9]+)*')
BASS_PATTERN = re.compile(r'(?:/([A-G][b#]?))?')
