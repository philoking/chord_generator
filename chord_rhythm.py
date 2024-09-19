import pygame
import random
import json
from midiutil import MIDIFile

# Initialize Pygame
pygame.init()

# Load rhythmic patterns from JSON file
with open('rhythmic_patterns.json', 'r') as f:
    rhythmic_patterns = json.load(f)["patterns"]

# Map chords to MIDI note lists (C major scale for simplicity)
chord_to_midi = {
    "I": [60, 64, 67],     # C Major (C, E, G)
    "ii": [62, 65, 69],    # D minor (D, F, A)
    "iii": [64, 67, 71],   # E minor (E, G, B)
    "IV": [65, 69, 72],    # F Major (F, A, C)
    "V": [67, 71, 74],     # G Major (G, B, D)
    "vi": [69, 72, 76],    # A minor (A, C, E)
    "vii°": [71, 74, 77],  # B diminished (B, D, F)
}

# Apply a random rhythm pattern
def apply_rhythm(chords):
    pattern = random.choice(rhythmic_patterns)["pattern"]
    rhythmic_progression = []
    
    # Iterate over the chord progression and apply the rhythm pattern
    for i in range(len(chords)):
        chord = chords[i]
        rhythm_pattern = pattern[i % len(pattern)]
        for duration in rhythm_pattern:
            if duration == "rest":
                rhythmic_progression.append(("rest", 1))  # Handle rest
            else:
                rhythmic_progression.append((chord, duration))
    
    return rhythmic_progression

# Generate MIDI from chord progression
def create_midi(chord_progression, tempo=120):
    rhythmic_progression = apply_rhythm(chord_progression)

    # Create MIDI file
    midi = MIDIFile(1)  # One track
    track = 0
    time = 0  # Start at the beginning
    midi.addTempo(track, time, tempo)

    for item in rhythmic_progression:
        chord = item[0]
        duration = item[1]

        if chord == "rest":
            time += duration  # Advance time for rests
        else:
            notes = chord_to_midi.get(chord, [60])  # Default to C major if not found
            for note in notes:
                midi.addNote(track, 0, note, time, duration, 100)
            time += duration

    # Save MIDI file to disk
    with open("output.mid", "wb") as output_file:
        midi.writeFile(output_file)

# Play MIDI file with pygame
def play_midi():
    pygame.mixer.music.load("output.mid")
    pygame.mixer.music.play()

    # Wait until the music finishes playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Main function
def main():
    chord_progression = ["I", "V", "IV", "I"]  # Example chord progression
    create_midi(chord_progression)
    print(f"Playing chord progression: {chord_progression}")
    play_midi()

    pygame.quit()

if __name__ == "__main__":
    main()
