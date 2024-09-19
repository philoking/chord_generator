from misc.chord_tokenizer import ChordTokenizer

test_chords = ["I", "IV", "Cm7", "F#maj7", "G/B", "Asus4", "Bbdim7", "invalid_chord"]
for chord in test_chords:
    token = ChordTokenizer.tokenize(chord)
    print(f"Original: {chord}, Tokenized: {token}, Type: {token.chord_type}")

    test_progression = "I-IVm-Cmaj7-F#m7b5/A#"
    tokens = ChordTokenizer.tokenize_progression(test_progression)
    print("\nProgression:", " ".join(str(token) for token in tokens))