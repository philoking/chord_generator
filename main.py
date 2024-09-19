import pygame
from chord_player import ChordProgressionPlayer

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
