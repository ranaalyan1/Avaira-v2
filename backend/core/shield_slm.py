import json
import httpx
import time
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel

class SLMClassification(BaseModel):
    intent: str
    is_malicious: bool
    risk_category: str
    confidence: float
    reasoning: str

class ShieldSLM:
    """
    Local Small Language Model intercept layer.
    Targets sub-50ms inference for real-time intent classification.
    """
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or os.environ.get("LOCAL_SLM_ENDPOINT", "http://localhost:11434/api/generate")
        self.model = os.environ.get("LOCAL_SLM_MODEL", "phi3") # Specialized for classification

    async def classify_intent(self, intent: Dict[str, Any]) -> SLMClassification:
        start_time = time.time()

        prompt = f"""
        Classification Task:
        Analyze this AI Agent Intent for security risks (Prompt Injection, PII Extraction, Scope Creep).

        Intent JSON: {json.dumps(intent)}

        Return ONLY valid JSON in this format:
        {{
          "intent": "short_description",
          "is_malicious": true/false,
          "risk_category": "none/pii/injection/unauthorized",
          "confidence": 0.0-1.0,
          "reasoning": "..."
        }}
        """

        try:
            # Attempt to call local inference (e.g. Ollama)
            async with httpx.AsyncClient(timeout=0.05) as client: # Strict 50ms timeout
                resp = await client.post(self.endpoint, json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                })
                data = resp.json()
                result = json.loads(data.get("response", "{}"))
                return SLMClassification(**result)
        except Exception:
            # Fallback to a fast heuristic classifier if local SLM is down or slow
            # In a real enterprise setup, this fallback would be a local regex-based engine
            return self._heuristic_fallback(intent)

    def _heuristic_fallback(self, intent: Dict[str, Any]) -> SLMClassification:
        action = str(intent.get("action", "")).lower()
        target = str(intent.get("target", "")).lower()

        malicious_keywords = ["delete", "rm -rf", "sudo", "password", "key", "token", "env"]
        is_malicious = any(k in action or k in target for k in malicious_keywords)

        return SLMClassification(
            intent=f"Heuristic: {action}",
            is_malicious=is_malicious,
            risk_category="unauthorized" if is_malicious else "none",
            confidence=0.5,
            reasoning="Fallback heuristic used due to SLM timeout/offline."
        )
