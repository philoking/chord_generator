import re
from enum import Enum, auto

class ChordType(Enum):
    ROMAN = auto()
    CHORD_SYMBOL = auto()
    INVALID = auto()

class ChordToken:
    def __init__(self, original, chord_type, root, quality=None, extensions=None, bass=None):
        self.original = original
        self.chord_type = chord_type
        self.root = root
        self.quality = quality
        self.extensions = extensions or []
        self.bass = bass

    def __str__(self):
        if self.chord_type == ChordType.ROMAN:
            return self.original
        elif self.chord_type == ChordType.CHORD_SYMBOL:
            chord = self.root + (self.quality or "")
            if self.extensions:
                chord += "".join(self.extensions)
            if self.bass:
                chord += f"/{self.bass}"
            return chord
        else:
            return "Invalid Chord"

class ChordTokenizer:
    ROMAN_PATTERN = r'^(IV|I{1,3}|VI{0,3}|iv|i{1,3}|vi{0,3})°?'
    ROOT_PATTERN = r'([A-G][b#]?)'
    QUALITY_PATTERN = r'(maj|min|m|M|\+|aug|dim)?'
    EXTENSIONS_PATTERN = r'((?:maj|add|sus|[0-9])*[0-9]+)*'
    BASS_PATTERN = r'(?:/([A-G][b#]?))?'

    @classmethod
    def tokenize(cls, chord_string):
        chord_string = chord_string.strip()
        
        # Check if it's a Roman numeral chord
        roman_match = re.match(cls.ROMAN_PATTERN, chord_string)
        if roman_match:
            return ChordToken(chord_string, ChordType.ROMAN, roman_match.group())

        # Parse chord symbol
        chord_pattern = f"{cls.ROOT_PATTERN}{cls.QUALITY_PATTERN}{cls.EXTENSIONS_PATTERN}{cls.BASS_PATTERN}$"
        match = re.match(chord_pattern, chord_string)
        
        if match:
            root, quality, extensions, bass = match.groups()
            extensions = cls._parse_extensions(extensions)
            return ChordToken(chord_string, ChordType.CHORD_SYMBOL, root, quality, extensions, bass)

        # If no match, return an invalid chord token
        return ChordToken(chord_string, ChordType.INVALID, None)

    @staticmethod
    def _parse_extensions(extensions_string):
        if not extensions_string:
            return []
        return re.findall(r'(?:maj|add|sus|[0-9])*[0-9]+', extensions_string)

    @classmethod
    def tokenize_progression(cls, progression_string):
        chords = progression_string.split('-')
        return [cls.tokenize(chord) for chord in chords]