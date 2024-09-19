import threading
from midiutil import MIDIFile
import pygame
import requests
import re
from enum import Enum, auto
import random
import music21
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

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

class ChordProgressionPlayer:
    def __init__(self):
        self.current_progression = []
        self.all_progressions = []
        self.is_playing = False
        self.should_stop = False
        self.tempo = 60
        self.key = 'C'
        self.is_minor = False
        self.progression_length = 4
        self.artist_to_emulate = None
        self.valid_keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def generate_progression_with_ollama(self):
        prompt = f"Generate a {self.progression_length}-chord progression"

        if self.artist_to_emulate:
            prompt += f" in the style of {self.artist_to_emulate}"

        prompt += f" in the key of {self.key}{'m' if self.is_minor else ''}. "
        prompt += "Use a mix of Roman numeral notation and chord names. "
        prompt += "Respond with only the chord progression, with chords separated by dashes. For example: I-Cmaj7-F-G7"

        if self.current_progression:
            previous_progression = '-'.join(self.format_chord(chord) for chord in self.current_progression)
            prompt += f" The previous progression was: {previous_progression}."

        logging.info(f"Sending prompt to Ollama: {prompt}")

        try:
            response = requests.post('http://192.168.0.214:7869/api/generate',
                                     json={"model": "llama3.1", "prompt": prompt, "stream": False})

            response.raise_for_status()
            response_json = response.json()
            progression_string = response_json['response'].strip()

            chord_tokens = tokenize_progression(progression_string)
            cleaned_progression = [format_chord_token(token) for token in chord_tokens if token['type'] != ChordType.INVALID]

            parsed_progression = self.parse_progression(cleaned_progression)
            return parsed_progression
        except Exception as e:
            logging.error(f"Error communicating with Ollama: {e}")
            return self.generate_random_progression()

    def parse_progression(self, progression):
        parsed = []
        key = music21.key.Key(self.key)
        tonic_chord = music21.roman.RomanNumeral('I', key)

        for chord in progression:
            try:
                token = tokenize_chord(chord)
                if token['type'] == ChordType.ROMAN:
                    parsed.append(music21.roman.RomanNumeral(token['root'], key))
                elif token['type'] == ChordType.CHORD_SYMBOL:
                    harmony = music21.harmony.ChordSymbol(format_chord_token(token))
                    if token['bass']:
                        harmony.bass(music21.pitch.Pitch(token['bass']))
                    parsed.append(harmony)
                else:
                    parsed.append(tonic_chord)
            except Exception:
                parsed.append(tonic_chord)

        while len(parsed) < self.progression_length:
            parsed.append(tonic_chord)

        return parsed[:self.progression_length]

    def generate_random_progression(self):
        degrees_minor = ['i', 'iv', 'v', 'VI', 'III', 'ii°', 'VII']
        degrees_major = ['I', 'IV', 'V', 'vi', 'ii', 'iii', 'viio']
        degrees = degrees_minor if self.is_minor else degrees_major
        return [music21.roman.RomanNumeral(degree, music21.key.Key(self.key)) for degree in random.choices(degrees, k=self.progression_length)]

    def format_chord(self, chord):
        if isinstance(chord, music21.roman.RomanNumeral):
            return chord.romanNumeral
        if isinstance(chord, music21.harmony.ChordSymbol):
            return chord.figure
        return str(chord)

    def apply_voice_leading(self, progression):
        def find_best_inversion(previous_pitches, current_pitches):
            possible_inversions = [
                current_pitches,
                [current_pitches[1], current_pitches[2], current_pitches[3], current_pitches[0].transpose(12)],
                [current_pitches[2], current_pitches[3], current_pitches[0].transpose(12), current_pitches[1].transpose(12)],
                [current_pitches[3], current_pitches[0].transpose(12), current_pitches[1].transpose(12), current_pitches[2].transpose(12)]
            ]

            def movement(inversion):
                return sum(min(abs(prev.midi - curr.midi), 12 - abs(prev.midi - curr.midi)) for prev, curr in zip(previous_pitches, inversion))

            return min(possible_inversions, key=movement)

        def normalize_octave(pitches, reference_pitch=60):  # Middle C (C4) is MIDI note 60
            normalized_pitches = []
            for pitch in pitches:
                while pitch.midi > reference_pitch + 12:
                    pitch = pitch.transpose(-12)
                while pitch.midi < reference_pitch - 12:
                    pitch = pitch.transpose(12)
                normalized_pitches.append(pitch)
            return normalized_pitches

        voice_led_progression = []
        previous_pitches = None

        for chord in progression:
            if isinstance(chord, (music21.roman.RomanNumeral, music21.harmony.ChordSymbol)):
                current_pitches = list(chord.pitches)

                while len(current_pitches) < 4:
                    current_pitches.append(current_pitches[-1].transpose(-12))
                while len(current_pitches) > 4:
                    current_pitches.pop()

                if previous_pitches is not None:
                    while len(previous_pitches) < 4:
                        previous_pitches.append(previous_pitches[-1].transpose(-12))
                    while len(previous_pitches) > 4:
                        previous_pitches.pop()

                    current_pitches = find_best_inversion(previous_pitches, current_pitches)
                    current_pitches = normalize_octave(current_pitches)

                    available_pitches = current_pitches[:]
                    for i in range(4):
                        closest_pitch = min(available_pitches, key=lambda p: abs(p.midi - previous_pitches[i].midi))
                        current_pitches[i] = closest_pitch
                        available_pitches.remove(closest_pitch)

                current_pitches = normalize_octave(current_pitches)
                previous_pitches = current_pitches[:]
                voice_led_chord = music21.chord.Chord(current_pitches)
                voice_led_progression.append(voice_led_chord)
            else:
                voice_led_progression.append(chord)

        return voice_led_progression

    def create_midi_file(self, progression, filename="chord_progression.mid"):
        voice_led_progression = self.apply_voice_leading(progression)

        midi = MIDIFile(1)
        track = 0
        time = 0
        midi.addTrackName(track, time, f"Chord Progression in {self.key}{'m' if self.is_minor else ''}")
        midi.addTempo(track, time, self.tempo)

        for chord in voice_led_progression:
            pitches = chord.pitches if isinstance(chord, (music21.chord.Chord, music21.roman.RomanNumeral, music21.harmony.ChordSymbol)) else []
            for pitch in pitches:
                midi.addNote(track, 0, pitch.midi, time, 2, 100) 
            time += 2

        with open(filename, "wb") as output_file:
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
        self.all_progressions.extend(progression)
        self.should_stop = False
        if not self.is_playing:
            self.is_playing = True
            threading.Thread(target=self.play_progression).start()

    def stop_playing(self):
        self.should_stop = True
        self.create_session_midi()

    def create_session_midi(self):
        if self.all_progressions:
            self.create_midi_file(self.all_progressions, "session_progression.mid")
            logging.info("Session MIDI file created: session_progression.mid")
        else:
            print("No progressions generated in this session.")

    def set_tempo(self, new_tempo):
        self.tempo = new_tempo

    def set_key(self, new_key):
        key = new_key.rstrip('m')
        if key in self.valid_keys:
            self.key = key
            self.is_minor = new_key.endswith('m')
            return True
        return False

    def set_progression_length(self, length):
        if 1 <= length <= 16:
            self.progression_length = length
            return True
        return False

    def set_artist(self, artist):
        self.artist_to_emulate = artist

def main():
    pygame.mixer.init()
    player = ChordProgressionPlayer()

    print("Welcome to the Chord Progression Chat!")
    print("Commands:")
    print("  generate - Generate and play a new chord progression")
    print("  tempo <bpm> - Change the tempo (e.g., 'tempo 100')")
    print("  key <key> - Change the key signature (e.g., 'key G' or 'key Em')")
    print("  length <num> - Set the number of chords in the progression (e.g., 'length 6')")
    print("  artist <name> - Set an artist to emulate (e.g., 'artist The Beatles')")
    print("  stop - Stop playing")
    print("  quit - Exit the program")

    while True:
        command = input("Enter a command: ").strip().lower()

        if command == "generate":
            new_progression = player.generate_progression_with_ollama()
            key_name = f"{player.key}{'m' if player.is_minor else ''}"
            formatted_progression = [player.format_chord(chord) for chord in new_progression]
            print(f"New progression: {'-'.join(formatted_progression)} in key of {key_name}")
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
        elif command.startswith("artist "):
            artist = ' '.join(command.split()[1:])
            player.set_artist(artist)
            print(f"Artist to emulate set to: {artist}")
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
