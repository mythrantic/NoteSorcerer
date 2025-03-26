import logging
import requests
import json
import asyncio
from typing import List, Dict, Generator, AsyncGenerator

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Ollama LLM models."""
    
    def __init__(self, host="localhost", port=7869):
        """Initialize the LLM service."""
        self.base_url = f"http://{host}:{port}"
        self.api_url = f"{self.base_url}/api"
        self.is_available = self._check_availability()
        self.default_model = "gemma:2b"
        
    def _check_availability(self):
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=2)
            if response.status_code == 200:
                logger.info("Ollama service is available")
                return True
            logger.warning(f"Ollama service returned status code: {response.status_code}")
            return False
        except Exception as e:
            logger.warning(f"Ollama service is not available: {e}")
            return False
    
    def get_available_models(self):
        """Get a list of available models from Ollama."""
        if not self.is_available:
            return []
        
        try:
            response = requests.get(f"{self.api_url}/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    async def generate_response(
        self, 
        messages: List[Dict], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """
        Generate a response from the LLM model using chat completion.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Model name to use (default: self.default_model)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 2000)
            
        Yields:
            String chunks of the generated response
        """
        if not self.is_available:
            yield "LLM service is not available. Please check if Ollama is running."
            return
        
        model = model or self.default_model
        url = f"{self.api_url}/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }
        
        try:
            logger.info(f"Generating response with model {model}")
            response = requests.post(url, json=payload, stream=True)
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            text_chunk = data["message"]["content"]
                            yield text_chunk
                        
                        # Break if this is the final message
                        if "done" in data and data["done"]:
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"Error: {str(e)}"
