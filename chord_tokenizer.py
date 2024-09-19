import re
from enum import Enum, auto
from utils import ChordType, ROMAN_PATTERN, ROOT_PATTERN, QUALITY_PATTERN, EXTENSIONS_PATTERN, BASS_PATTERN

def tokenize_chord(chord_string):
    chord_string = chord_string.strip()

    roman_match = ROMAN_PATTERN.match(chord_string)
    if roman_match:
        return {
            'original': chord_string,
            'type': ChordType.ROMAN,
            'root': roman_match.group(),
            'quality': None,
            'extensions': None,
            'bass': None
        }

    chord_pattern = f"{ROOT_PATTERN.pattern}{QUALITY_PATTERN.pattern}{EXTENSIONS_PATTERN.pattern}{BASS_PATTERN.pattern}$"
    match = re.match(chord_pattern, chord_string)

    if match:
        root, quality, extensions, bass = match.groups()
        return {
            'original': chord_string,
            'type': ChordType.CHORD_SYMBOL,
            'root': root,
            'quality': quality,
            'extensions': re.findall(r'(?:maj|add|sus|[0-9])*[0-9]+', extensions) if extensions else None,
            'bass': bass
        }

    return {
        'original': chord_string,
        'type': ChordType.INVALID,
        'root': None,
        'quality': None,
        'extensions': None,
        'bass': None
    }

def format_chord_token(token):
    if token['type'] == ChordType.ROMAN:
        return token['original']
    if token['type'] == ChordType.CHORD_SYMBOL:
        chord = token['root'] + (token['quality'] or "")
        if token['extensions']:
            chord += "".join(token['extensions'])
        if token['bass']:
            chord += f"/{token['bass']}"
        return chord
    return "Invalid Chord"

def tokenize_progression(progression_string):
    chords = progression_string.split('-')
    return [tokenize_chord(chord) for chord in chords]
