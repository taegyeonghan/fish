"""
LLM
OpenAI
"""

import json
import re
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config


class LLMClient:
    """LLM"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY ")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 16384,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        
        
        Args:
            messages: 
            temperature: 
            max_tokens: token
            response_format: （JSON）
            
        Returns:
            
        """
        # gpt-5 계열은 max_completion_tokens, 나머지는 max_tokens
        token_key = "max_completion_tokens" if "gpt-5" in self.model else "max_tokens"
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            token_key: max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        # （MiniMax M2.5）content<think>，
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content
    
    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 16384
    ) -> Dict[str, Any]:
        """
        JSON
        
        Args:
            messages: 
            temperature: 
            max_tokens: token
            
        Returns:
            JSON
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        # markdown
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        return self._parse_json_robust(cleaned_response)

    @staticmethod
    def _parse_json_robust(text: str) -> Dict[str, Any]:
        """Robustly parse JSON from LLM output, handling common errors."""
        # 1. Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Strip trailing extra braces/brackets one at a time
        attempt = text
        for _ in range(5):
            attempt = attempt.rstrip()
            if len(attempt) < 2:
                break
            # Remove last char if it creates valid JSON
            trimmed = attempt[:-1]
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError:
                attempt = trimmed

        # 3. Find balanced JSON by counting braces
        start = text.find('{')
        if start >= 0:
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                c = text[i]
                if escape:
                    escape = False
                    continue
                if c == '\\':
                    escape = True
                    continue
                if c == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            break

        raise ValueError(f"Invalid JSON from LLM: {text[:300]}")
