import os
import json
import urllib.request
import urllib.error
from depattern.providers.base import BaseProvider
from depattern.config import Config

class GeminiProvider(BaseProvider):
    def __init__(self, config: Config):
        self.config = config
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            # Fallback to config file if present
            self.api_key = config.data.get("llm", {}).get("api_key")
            
        self.model = config.llm_model
        
    def generate(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise ValueError(
                "Gemini API key is missing. Please set the GEMINI_API_KEY environment variable "
                "or define [llm].api_key in depattern.toml."
            )
            
        # Official endpoint: v1beta/models/{model}:generateContent
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [
                    {"text": system_instruction}
                ]
            }
            
        headers = {
            "Content-Type": "application/json"
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                
                # Check for errors in response
                if "candidates" not in res_data or not res_data["candidates"]:
                    raise ValueError(f"Gemini API responded with no candidates: {json.dumps(res_data)}")
                    
                candidate = res_data["candidates"][0]
                if "content" not in candidate or "parts" not in candidate["content"]:
                    # Check for safety blocks or finish reason
                    finish_reason = candidate.get("finishReason", "UNKNOWN")
                    raise ValueError(f"Generation failed. Finish reason: {finish_reason}. Content may be blocked.")
                    
                parts = candidate["content"]["parts"]
                text_content = "".join(part.get("text", "") for part in parts)
                return text_content
                
        except urllib.error.HTTPError as e:
            err_content = e.read().decode("utf-8")
            try:
                err_json = json.loads(err_content)
                err_msg = err_json.get("error", {}).get("message", err_content)
            except Exception:
                err_msg = err_content
            raise RuntimeError(f"Gemini API request failed ({e.code}): {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Gemini API: {e}")
