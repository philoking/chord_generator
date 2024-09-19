import requests
import json

# Define the Ollama instance details
ollama_url = "http://192.168.0.214:7869"
MODEL = "mistral-nemo:latest"

# Define headers if needed
HEADERS = {
    "Content-Type": "application/json"
}

# Initialize the conversation with a system prompt
def start_conversation(system_prompt):
    url = f"{ollama_url}/api/v1/chat/completions"
    
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    
    # Print the raw response to check its content before parsing
    print(f"Raw response: {response.text}")
    
    try:
        response_json = response.json()
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return None, None
    
    if response.status_code == 200:
        # Return the conversation ID or session for continued interaction
        return response_json["id"], response_json["choices"][0]["message"]["content"]
    else:
        print(f"Error starting conversation: {response.text}")
        return None, None

# Continue conversation by sending a song idea prompt
def continue_conversation(conversation_id, song_prompt):
    url = f"{ollama_url}/api/v1/chat/completions"
    
    data = {
        "model": MODEL,
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": "user",
                "content": song_prompt
            }
        ]
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    response_json = response.json()
    
    if response.status_code == 200:
        return response_json["choices"][0]["message"]["content"]
    else:
        print(f"Error continuing conversation: {response.text}")
        return None

# Example usage of the script
if __name__ == "__main__":
    # Define the system prompt and initial user song idea prompt
    system_prompt = "You are a songwriting assistant. Help me come up with ideas for a new song."
    song_idea_prompt = "I want a song in the style of ambient techno, with a slow build and dreamy melodies. Give me a detailed breakdown of how I should structure the song."

    # Start the conversation
    conversation_id, system_response = start_conversation(system_prompt)
    
    if conversation_id:
        print(f"System response: {system_response}")

        # Send a song idea prompt and continue the conversation
        song_details = continue_conversation(conversation_id, song_idea_prompt)
        print(f"Song details: {song_details}")
