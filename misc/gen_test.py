import threading
import time
import random
from midiutil import MIDIFile
import pygame

class ChordProgressionPlayer:
    def __init__(self):
        self.current_progression = []
        self.is_playing = False
        self.should_stop = False
        self.tempo = 120
        self.key = 'C'
        self.is_minor = False
        self.progression_length = 4
        self.scale_degrees = {
            'i': 0, 'ii': 2, 'iii': 4, 'iv': 5, 'v': 7, 'vi': 9, 'vii': 11,
            'I': 0, 'II': 2, 'III': 4, 'IV': 5, 'V': 7, 'VI': 9, 'VII': 11
        }
        self.key_offsets = {
            'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
            'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
        }

    def generate_progression(self):
        if self.is_minor:
            degrees = ['i', 'iv', 'v', 'VI', 'III', 'ii°', 'VII']  # Extended minor options
        else:
            degrees = ['I', 'IV', 'V', 'vi', 'ii', 'iii', 'viio']  # Extended major options
        return [random.choice(degrees) for _ in range(self.progression_length)]

    def create_midi_file(self, progression):
        midi = MIDIFile(1)
        track = 0
        time = 0
        key_name = f"{self.key}{'m' if self.is_minor else ''}"
        midi.addTrackName(track, time, f"Chord Progression in {key_name}")
        midi.addTempo(track, time, self.tempo)

        for degree in progression:
            chord_root = (self.key_offsets[self.key] + self.scale_degrees[degree.rstrip('o')]) % 12
            
            if self.is_minor:
                if degree.islower() and 'o' not in degree:  # Minor chords
                    chord = [chord_root, (chord_root + 3) % 12, (chord_root + 7) % 12]
                elif degree.isupper():  # Major chord (e.g., VI in minor key)
                    chord = [chord_root, (chord_root + 4) % 12, (chord_root + 7) % 12]
                else:  # Diminished chord (ii° in minor key)
                    chord = [chord_root, (chord_root + 3) % 12, (chord_root + 6) % 12]
            else:
                if degree.isupper():  # Major chords
                    chord = [chord_root, (chord_root + 4) % 12, (chord_root + 7) % 12]
                elif degree.islower() and 'o' not in degree:  # Minor chords
                    chord = [chord_root, (chord_root + 3) % 12, (chord_root + 7) % 12]
                else:  # Diminished chord (viio in major key)
                    chord = [chord_root, (chord_root + 3) % 12, (chord_root + 6) % 12]
            
            for note in chord:
                midi.addNote(track, 0, note + 60, time, 2, 100)  # Adding 60 to start from middle C
            time += 2

        with open("chord_progression.mid", "wb") as output_file:
            midi.writeFile(output_file)

    def play_progression(self):
        while not self.should_stop:
            self.create_midi_file(self.current_progression)
            pygame.mixer.music.load("chord_progression.mid")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not self.should_stop:
                pygame.time.Clock().tick(10)
        self.is_playing = False

    def start_playing(self, progression):
        self.current_progression = progression
        self.should_stop = False
        if not self.is_playing:
            self.is_playing = True
            threading.Thread(target=self.play_progression).start()

    def stop_playing(self):
        self.should_stop = True

    def set_tempo(self, new_tempo):
        self.tempo = new_tempo

    def set_key(self, new_key):
        key = new_key.rstrip('m')
        if key in self.key_offsets:
            self.key = key
            self.is_minor = new_key.endswith('m')
            return True
        return False

    def set_progression_length(self, length):
        if 1 <= length <= 16:  # Limiting to a reasonable range
            self.progression_length = length
            return True
        return False

def main():
    pygame.mixer.init()
    player = ChordProgressionPlayer()

    print("Welcome to the Chord Progression Chat!")
    print("Commands:")
    print("  generate - Generate and play a new chord progression")
    print("  tempo <bpm> - Change the tempo (e.g., 'tempo 100')")
    print("  key <key> - Change the key signature (e.g., 'key G' or 'key Em')")
    print("  length <num> - Set the number of chords in the progression (e.g., 'length 6')")
    print("  stop - Stop playing")
    print("  quit - Exit the program")

    while True:
        command = input("Enter a command: ").strip().lower()

        if command == "generate":
            new_progression = player.generate_progression()
            key_name = f"{player.key}{'m' if player.is_minor else ''}"
            print(f"New progression: {' '.join(new_progression)} in key of {key_name}")
            player.stop_playing()
            player.start_playing(new_progression)
        elif command.startswith("tempo "):
            try:
                new_tempo = int(command.split()[1])
                if 40 <= new_tempo <= 240:
                    player.set_tempo(new_tempo)
                    print(f"Tempo changed to {new_tempo} BPM.")
                    if player.is_playing:
                        print("Restart playback to apply the new tempo.")
                else:
                    print("Tempo should be between 40 and 240 BPM.")
            except (IndexError, ValueError):
                print("Invalid tempo command. Use 'tempo <bpm>'.")
        elif command.startswith("key "):
            new_key = command.split()[1].capitalize()
            if player.set_key(new_key):
                print(f"Key signature changed to {new_key}.")
                if player.is_playing:
                    print("Restart playback to apply the new key.")
            else:
                print("Invalid key. Please use C, C#, D, D#, E, F, F#, G, G#, A, A#, or B, optionally followed by 'm' for minor.")
        elif command.startswith("length "):
            try:
                new_length = int(command.split()[1])
                if player.set_progression_length(new_length):
                    print(f"Progression length set to {new_length} chords.")
                else:
                    print("Invalid length. Please choose a number between 1 and 16.")
            except (IndexError, ValueError):
                print("Invalid length command. Use 'length <number>'.")
        elif command == "stop":
            player.stop_playing()
            print("Playback stopped.")
        elif command == "quit":
            player.stop_playing()
            print("Goodbye!")
            break
        else:
            print("Unknown command. Please try again.")

if __name__ == "__main__":
    main()