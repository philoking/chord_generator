import json
import requests
import re
from music21 import stream, harmony, tempo, key, meter, duration
from ollama import get_song_concept

ollama_url = "http://192.168.0.214:7869/api/generate"

def get_song_concept(ollama_url):
    # Create the system prompt and the user prompt
    user_prompt = """
    Generate an ambient electronic music track in JSON format with song details, structure, and chord progressions, following this template:
    
    {
        "song_details": {
            "title": "<unique_title>",
            "artist": "AI Composer",
            "key_signature": "<unique_key_signature>",
            "tempo": "<unique_tempo>",
            "time_signature": "<unique_time_signature>"
        },
        "song_structure": [
            {"section": "intro", "measures": <unique_intro_measures>},
            {"section": "verse1", "measures": <unique_verse1_measures>},
            {"section": "pre_chorus", "measures": <unique_pre_chorus_measures>},
            {"section": "chorus", "measures": <unique_chorus_measures>},
            {"section": "verse2", "measures": <unique_verse2_measures>},
            {"section": "pre_chorus", "measures": <unique_pre_chorus_measures>},
            {"section": "chorus", "measures": <unique_chorus_measures>},
            {"section": "bridge", "measures": <unique_bridge_measures>},
            {"section": "outro", "measures": <unique_outro_measures>}
        ],
        "progressions": {
            "intro": {"chords": [<list_of_chords_with_duration>]},
            "verse1": {"chords": [<list_of_chords_with_duration>]},
            "pre_chorus": {"chords": [<list_of_chords_with_duration>]},
            "chorus": {"chords": [<list_of_chords_with_duration>]},
            "verse2": {"chords": [<list_of_chords_with_duration>]},
            "bridge": {"chords": [<list_of_chords_with_duration>]},
            "outro": {"chords": [<list_of_chords_with_duration>]}
        }
    }

    Return only the JSON object.
    """

    try:
        # Construct the JSON payload with the snapshot image
        prompt = {
            "model": "llama3.1",
            "prompt": user_prompt,
            "stream": False
        }

        print(f"Sending ollama request.")

        # Send the snapshot image to Ollama
        response = requests.post(ollama_url, json=prompt)
        response.raise_for_status()

        # Extract the 'response' field from the full JSON response
        full_response = response.json()
        ollama_response = full_response.get('response')

        # Print the 'response' field
        print(f"Ollama response: {ollama_response}")

        # Parse the JSON string in the response
        song_data = json.loads(ollama_response)

        # Remove the extra backticks and "json" text if present
        cleaned_response = ollama_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]  # Remove "```json"
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]  # Remove trailing "```"
        
        # Parse the cleaned JSON string in the response
        song_data = json.loads(cleaned_response)

        return song_data

    except requests.RequestException as e:
        print(f"Error processing: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {ollama_response}")
        return None
    
def create_chord_stream(chord_data, key_signature, tempo_value, time_signature):
    """Create a music21 stream from chord data, key, tempo, and time signature."""
    chord_stream = stream.Part()

    # Split key signature into tonic and mode
    key_parts = key_signature.split()
    tonic = key_parts[0]
    mode = key_parts[1] if len(key_parts) > 1 else 'major'

    # Set key signature, tempo, and time signature
    chord_stream.append(key.Key(tonic, mode))
    chord_stream.append(tempo.MetronomeMark(number=tempo_value))
    ts = meter.TimeSignature(time_signature)
    chord_stream.append(ts)

    measure = stream.Measure()
    measure_duration = 0
    beats_per_measure = ts.numerator

    for chord_name, chord_duration in chord_data:
        c = harmony.ChordSymbol(chord_name)
        c.quarterLength = chord_duration
        
        # If adding this chord would exceed the measure duration, start a new measure
        if measure_duration + chord_duration > beats_per_measure:
            # Fill the remainder of the current measure
            remainder = beats_per_measure - measure_duration
            if remainder > 0:
                filler_chord = harmony.ChordSymbol(chord_name)
                filler_chord.quarterLength = remainder
                measure.append(filler_chord)
            
            chord_stream.append(measure)
            measure = stream.Measure()
            measure_duration = 0

        measure.append(c)
        measure_duration += chord_duration

        # If the measure is full, add it to the stream and start a new one
        if measure_duration == beats_per_measure:
            chord_stream.append(measure)
            measure = stream.Measure()
            measure_duration = 0

    # Add any remaining chords in the last measure
    if measure_duration > 0:
        # Fill the remainder of the last measure if needed
        if measure_duration < beats_per_measure:
            remainder = beats_per_measure - measure_duration
            filler_chord = harmony.ChordSymbol(chord_name)  # Use the last chord to fill
            filler_chord.quarterLength = remainder
            measure.append(filler_chord)
        chord_stream.append(measure)

    return chord_stream

def create_section(section_name, measures, progression, tempo_value, key_signature, time_signature):
    """Create a section of the song based on progression and measures."""
    if section_name not in progression or "chords" not in progression[section_name] or not progression[section_name]["chords"]:
        raise KeyError(f"Section '{section_name}' or its chords are not defined in the progression data.")

    chord_data = progression[section_name]["chords"]
    section_stream = create_chord_stream(chord_data, key_signature, tempo_value, time_signature)

    # Ensure the section has the correct number of measures
    current_measures = len(section_stream.getElementsByClass('Measure'))
    if current_measures < measures:
        # Repeat the progression to fill the required measures
        extra_measures_needed = measures - current_measures
        measures_to_repeat = section_stream.getElementsByClass('Measure')
        for i in range(extra_measures_needed):
            new_measure = stream.Measure()
            source_measure = measures_to_repeat[i % len(measures_to_repeat)]
            for element in source_measure.elements:
                if isinstance(element, harmony.ChordSymbol):
                    # Create a new ChordSymbol with the same properties
                    new_chord = harmony.ChordSymbol(element.figure)
                    new_chord.quarterLength = element.quarterLength
                    new_measure.append(new_chord)
                else:
                    # For other types of elements, we can use copy() method
                    new_measure.append(element.copy())
            section_stream.append(new_measure)

    return section_stream

def main():
    song_data = get_song_concept(ollama_url)
    if song_data is None:
        print("Failed to get song concept. Exiting.")
        return

    try:
        song_details = song_data["song_details"]
        song_structure = song_data["song_structure"]
        progressions = song_data["progressions"]

        key_signature = song_details["key_signature"]
        tempo_value = int(song_details["tempo"].split()[0])  # Extract the numeric value
        time_signature = song_details["time_signature"]

        # ... [rest of the function remains the same] ...

    except KeyError as e:
        print(f"Error: Missing expected key in song data: {e}")
        return
    except ValueError as e:
        print(f"Error: Invalid value in song data: {e}")
        return
    
    #song_data = get_song_concept(ollama_url)

    song_details = song_data["song_details"]
    song_structure = song_data["song_structure"]
    progressions = song_data["progressions"]

    key_signature = song_details["key_signature"]
    tempo_value = int(song_details["tempo"])
    time_signature = song_details["time_signature"]

    # Create a single stream for the entire song
    song_stream = stream.Stream()

    # Parse the key signature
    key_parts = key_signature.split()
    tonic = key_parts[0]
    mode = key_parts[1] if len(key_parts) > 1 else 'major'  # Default to major if not provided

    # Add song details to the stream
    song_stream.append(key.Key(tonic, mode))
    song_stream.append(tempo.MetronomeMark(number=tempo_value))
    song_stream.append(meter.TimeSignature(time_signature))

    # Add each section to the song
    for section in song_structure:
        section_name = section["section"]
        measures = section["measures"]
        print(f"Creating section: {section_name} for {measures} measures")
        section_stream = create_section(section_name, measures, progressions, tempo_value, key_signature, time_signature)
        # Append the section's content to the main stream
        for element in section_stream.elements:
            song_stream.append(element)

    # Create a Score object and add the song stream
    score = stream.Score()
    score.insert(0, song_stream)

    # Save the MIDI file
    output_file = "generated_song.mid"
    score.write('midi', fp=output_file)
    print(f"MIDI file saved as: {output_file}")

if __name__ == "__main__":
    main()