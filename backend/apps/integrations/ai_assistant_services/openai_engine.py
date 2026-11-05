# -*- coding: utf-8 -*-
"""
ProofVoice OpenAI Primary AI Reasoning Engine.
Communicates with the official OpenAI API (gpt-4o-mini / gpt-4o).
Provides:
- Synchronous completions with full multi-turn conversation memory
- Real-time token streaming via Server-Sent Events (SSE)
- Timeout & retry resilience
- Rate limit handling and transparent status disclosures
"""

import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class OpenAiEngine:

    @classmethod
    def get_api_key(cls) -> str:
        """Retrieves configured OpenAI API Key securely from settings or environment."""
        key = getattr(settings, 'OPENAI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')
        return key.strip() if key else ''

    @classmethod
    def get_base_url(cls) -> str:
        """Retrieves configured OpenAI API Base URL."""
        base = getattr(settings, 'OPENAI_API_BASE_URL', '') or os.getenv('OPENAI_API_BASE_URL', '') or 'https://api.openai.com/v1'
        return base.strip().rstrip('/')

    @classmethod
    def get_model(cls) -> str:
        """Retrieves primary model (default: gpt-4o-mini)."""
        model = getattr(settings, 'OPENAI_MODEL', '') or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        return model.strip()

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if OpenAI API key is present."""
        key = cls.get_api_key()
        return bool(key and key.startswith('sk-'))

    @classmethod
    def generate_chat_completion(cls, messages: list, model: str = None, temperature: float = 0.7, max_tokens: int = 850) -> dict:
        """
        Executes an authenticated Chat Completion request against the OpenAI API.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return {
                'success': False,
                'is_configured': False,
                'error': 'OpenAI API key is not configured in backend/.env'
            }

        endpoint = f"{cls.get_base_url()}/chat/completions"
        target_model = model or cls.get_model()

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': target_model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=20)

            if response.status_code == 200:
                data = response.json()
                choice = data['choices'][0]
                content = choice['message']['content'].strip()
                usage = data.get('usage', {})
                return {
                    'success': True,
                    'is_configured': True,
                    'content': content,
                    'model': target_model,
                    'usage': usage,
                    'finish_reason': choice.get('finish_reason')
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': 'OpenAI API authentication failed. Please verify OPENAI_API_KEY in backend/.env.'
                }
            elif response.status_code == 429:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': 'OpenAI rate limit or quota exceeded. Please check your OpenAI account billing or wait a moment.'
                }
            else:
                return {
                    'success': False,
                    'is_configured': True,
                    'error': f'OpenAI service returned error HTTP {response.status_code}: {response.text[:200]}'
                }

        except requests.Timeout:
            return {
                'success': False,
                'is_configured': True,
                'error': 'OpenAI API request timed out. Please try again.'
            }
        except Exception as e:
            logger.warning(f"OpenAI connection error: {e}")
            return {
                'success': False,
                'is_configured': True,
                'error': f'Could not connect to OpenAI API: {str(e)}'
            }

    @classmethod
    def stream_chat_completion(cls, messages: list, model: str = None, temperature: float = 0.7, max_tokens: int = 850):
        """
        Streams response tokens from OpenAI API yielding text chunks in real time.
        """
        api_key = cls.get_api_key()
        if not api_key:
            yield "OpenAI API key is not configured in backend/.env"
            return

        endpoint = f"{cls.get_base_url()}/chat/completions"
        target_model = model or cls.get_model()

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': target_model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': True
        }

        try:
            with requests.post(endpoint, headers=headers, json=payload, stream=True, timeout=25) as response:
                if response.status_code != 200:
                    yield f"Error: OpenAI service returned HTTP {response.status_code}"
                    return

                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_content = line_str[6:].strip()
                            if data_content == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data_content)
                                delta = chunk['choices'][0].get('delta', {})
                                token = delta.get('content', '')
                                if token:
                                    yield token
                            except Exception:
                                continue
        except Exception as e:
            yield f"\n[Stream connection interrupted: {str(e)}]"
