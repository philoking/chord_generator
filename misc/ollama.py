import requests
import json
import re

def get_song_concept(ollama_url):
    # Create the system prompt and the user prompt
    user_prompt = """
    Generate a song structure in JSON format with the following format:
    [
        {"section": "intro", "chords": ["chord1", "chord2", "chord3", "chord4"], "rhythm": "1/4, 1/4, 1/4, 1/4"},
        {"section": "verse", "chords": ["chord1", "chord2", "chord3", "chord4", "chord1", "chord2", "chord3", "chord4"], "rhythm": "1/4, 1/4, 1/2, 1/4"},
        {"section": "chorus", "chords": ["chord1", "chord2", "chord3", "chord4", "chord1", "chord2", "chord3", "chord4"], "rhythm": "1/4, 1/4, 1/4, 1/4"},
        {"section": "verse", "chords": ["chord1", "chord2", "chord3", "chord4", "chord1", "chord2", "chord3", "chord4"], "rhythm": "1/4, 1/4, 1/2, 1/4"},
        {"section": "chorus", "chords": ["chord1", "chord2", "chord3", "chord4", "chord1", "chord2", "chord3", "chord4"], "rhythm": "1/4, 1/4, 1/4, 1/4"},
        {"section": "outro", "chords": ["chord1", "chord2", "chord3", "chord4"], "rhythm": "1/4, 1/4, 1/4, 1/4"}
    ]

    - Each section must have unique chords chosen from a standard set of chords (e.g., C, G, Am, F, Dm, Em, etc.).
    - The rhythm should follow the pattern in the format "1/4, 1/4, 1/4, 1/4" or similar variations for each section.
    - Ensure the song structure is consistent with common pop/rock styles.


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

        # Remove the extra backticks and "json" text if present
        cleaned_response = ollama_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]  # Remove "```json"
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]  # Remove trailing "```"

        # Print the 'response' field
        print(f"{cleaned_response}")


    except requests.RequestException as e:
        print(f"Error processing: {e}")
        return False