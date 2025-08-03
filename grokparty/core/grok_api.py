import aiohttp
from typing import List, Dict


class GrokAPI:
    """Handles communication with Grok API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.x.ai/v1"
        self.models = [
    {"id": "grok-4", "name": "Grok 4"},
    {"id": "grok-3-mini", "name": "Grok 3 Mini"},
    {"id": "grok-3-fast", "name": "Grok 3 Fast"},
    {"id": "grok-3-mini-fast", "name": "Grok 3 Mini Fast"},
    {"id": "grok-3", "name": "Grok 3"}
        ]
    
    async def send_request(self, model: str, messages: List[Dict], temperature: float = 0.8) -> str:
        """Send a request to Grok API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "search_parameters": {
                "mode": "auto",
                "return_citations": True,
                "max_search_results": 10,
                "sources": [
                    {"type": "web", "safe_search": True, "country": "us"},
                    {"type": "news", "safe_search": True, "country": "us"},
                    {"type": "x"}
                ]
            },
            "temperature": temperature,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
