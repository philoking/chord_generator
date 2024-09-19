import threading
import pygame
import music21
import random
import logging
from midiutil import MIDIFile
from chord_tokenizer import tokenize_progression, format_chord_token, tokenize_chord
from ollama_interface import OllamaAPI
from utils import ChordType

logging.basicConfig(level=logging.INFO)

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
        self.ollama_api = OllamaAPI("http://192.168.0.214:7869")  # Update with your actual Ollama instance

    def generate_progression_with_ollama(self):
        prompt = f"Generate a {self.progression_length}-chord progression"

        if self.artist_to_emulate:
            prompt += f" in the style of {self.artist_to_emulate}"

        prompt += f" in the key of {self.key}{'m' if self.is_minor else ''}. "
        prompt += "Use only chord names."
        prompt += "Respond with only the chord progression, with chords in root + quality, separated by dashes. For example: G-Cmaj7-F-G7"

        if self.current_progression:
            previous_progression = '-'.join(self.format_chord(chord) for chord in self.current_progression)
            prompt += f" The previous progression was: {previous_progression}."

        logging.info(f"Sending prompt to Ollama: {prompt}")

        progression_string = self.ollama_api.generate_progression_with_ollama(prompt)
        print(progression_string)
        
        if progression_string:
            chord_tokens = tokenize_progression(progression_string)
            cleaned_progression = [format_chord_token(token) for token in chord_tokens if token['type'] != ChordType.INVALID]

            parsed_progression = self.parse_progression(cleaned_progression)
            return parsed_progression
        else:
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

    def create_midi_file(self, progression, filename="midi_output/chord_progression.mid"):
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
            pygame.mixer.music.load("midi_output/chord_progression.mid")
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
            self.create_midi_file(self.all_progressions, "midi_output/session_progression.mid")
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
