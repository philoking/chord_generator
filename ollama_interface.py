import requests
import logging

logging.basicConfig(level=logging.INFO)

class OllamaAPI:
    def __init__(self, api_url):
        self.api_url = api_url

    def generate_progression_with_ollama(self, prompt):
        try:
            response = requests.post(f'{self.api_url}/api/generate',
                                     json={"model": "llama3.1", "prompt": prompt, "stream": False})
            response.raise_for_status()
            return response.json()['response'].strip()
        except Exception as e:
            logging.error(f"Error communicating with Ollama: {e}")
            return None
