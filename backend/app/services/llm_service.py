# backend/app/services/llm_service.py
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import time
import os
import google.generativeai as genai
from app.config import settings

# --- BASE CLIENT ---
class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: List[Dict[str, str]], **kwargs) -> str:
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass

# --- GEMINI CLIENT ---
class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        if not api_key:
            raise ValueError("Gemini API key is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        print(f"✅ Gemini client initialized (model: {model})")

    async def complete(self, messages: List[Dict[str, str]], temperature: float = 0.3, **kwargs) -> str:
        try:
            # Convert messages to Gemini format (history + last user message)
            chat_history = []
            last_message = ""

            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                content = msg["content"]
                
                if msg["role"] == "system":
                    last_message += f"System Instruction: {content}\n\n"
                    continue
                if msg == messages[-1] and msg["role"] == "user":
                    last_message += content
                else:
                    chat_history.append({"role": role, "parts": [content]})

            chat = self.model.start_chat(history=chat_history)
            
            response = await chat.send_message_async(
                last_message,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            return response.text
            
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

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
            if self.provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                LLMService._client = GeminiClient(api_key=api_key)
            else:
                # Fallback or other providers
                raise ValueError(f"Provider {self.provider} not configured")
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
            "tokens_used": 0,
            "model": "gemini-pro",
            "provider": self.provider,
            "generation_time_ms": elapsed
        }

    def get_info(self):
        return {"provider": self.provider, "model": "gemini-pro"}

llm_service = LLMService()
def get_llm_service(): return llm_service