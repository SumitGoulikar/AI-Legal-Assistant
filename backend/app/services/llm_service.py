# backend/app/services/llm_service.py
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import time
import os
import httpx
from app.config import settings

class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass
    
    def count_tokens(self, text: str) -> int:
        return len(text) // 4

# --- OLLAMA CLIENT ---
class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.client = httpx.AsyncClient(timeout=120.0) # 2 min timeout for local AI
        print(f"✅ Ollama client initialized ({model})")

    async def complete(self, messages: List[Dict[str, str]], temperature: float = 0.3, **kwargs) -> str:
        # Convert messages to Ollama prompt format
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        prompt += "Assistant: "

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")
            
        except Exception as e:
            print(f"❌ Ollama Error: {e}")
            return "Error: Could not connect to local AI."

# --- FACTORY ---
class LLMService:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    def _get_client(self):
        if LLMService._client is None:
            if self.provider == "ollama":
                base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                model = os.getenv("OLLAMA_MODEL", "gemma:2b")
                LLMService._client = OllamaClient(base_url, model)
            else:
                # Default/Mock fallback
                print(f"⚠️ Provider '{self.provider}' not configured. Check .env")
        return LLMService._client

    @property
    def client(self):
        return self._get_client()

    async def generate_response(self, messages, temperature=0.3, max_tokens=1000):
        start = time.time()
        client = self.client
        response_text = await client.complete(messages, temperature=temperature)
        elapsed = int((time.time() - start) * 1000)
        
        return {
            "response": response_text,
            "tokens_used": len(response_text) // 4,
            "model": os.getenv("OLLAMA_MODEL"),
            "provider": "ollama",
            "generation_time_ms": elapsed
        }

    def get_info(self):
        return {"provider": "ollama", "model": os.getenv("OLLAMA_MODEL")}

llm_service = LLMService()
def get_llm_service(): return llm_service