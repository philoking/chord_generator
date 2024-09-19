from music21 import key, roman, corpus
from misc.midi_input import capture_input
from misc.ollama import get_song_concept

ollama_url = "http://192.168.0.214:7869/api/generate"

def generate_scale_and_harmonize(input_key):
    # Create a key object
    key_obj = key.Key(input_key)
    
    # Harmonize the scale by creating triads for each scale degree
    for scale_degree in range(1, 8):  # Scale degrees 1 through 7
        # Use Roman numerals to create chords based on the scale degree
        roman_chord = roman.RomanNumeral(scale_degree, key_obj)
        # Print the Roman numeral and the corresponding chord
        print(f"{roman_chord.figure}: {roman_chord.pitchedCommonName}")

if __name__ == '__main__':
    # Example usage
    input_key = "ab"  # You can change this to any key, e.g., "D", "E", "F#"
    # generate_scale_and_harmonize(input_key)
    get_song_concept(ollama_url)


