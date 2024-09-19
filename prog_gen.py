import music21
import random
from chord_tokenizer import tokenize_chord, ChordType, format_chord_token

def distribute_chords_across_bars(self, progression):
    chords_per_bar = max(1, len(progression) // self.bars)
    distributed_progression = []

    for i in range(self.bars):
        start = i * chords_per_bar
        end = min(start + chords_per_bar, len(progression))  # Ensure 'end' doesn't exceed the progression length
        bar_chords = progression[start:end]

        # If the bar is empty, or there are fewer chords than expected for this bar, hold the last chord in progression
        if not bar_chords:
            if distributed_progression:
                bar_chords.append(distributed_progression[-1])  # Repeat the last chord from the previous bar
        elif len(bar_chords) < chords_per_bar:
            bar_chords.append(bar_chords[-1])  # Repeat the last chord in the current bar

        distributed_progression.extend(bar_chords)

    return distributed_progression

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