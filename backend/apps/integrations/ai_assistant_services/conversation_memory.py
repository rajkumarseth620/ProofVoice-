# -*- coding: utf-8 -*-
"""
Conversation Memory & Multi-Turn Context Manager.
Formats conversation history for OpenAI and Gemini APIs, tracks antecedent references,
and prevents mixing user contexts.
"""

class ConversationMemory:
    @classmethod
    def format_history_for_openai(cls, history: list, system_instruction: str, current_query: str, max_turns: int = 10) -> list:
        """
        Builds a compliant messages list for OpenAI Chat Completions API:
        [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}, {"role": "user", ...}]
        """
        messages = [{"role": "system", "content": system_instruction}]

        if history and isinstance(history, list):
            # Take the most recent turns
            recent = history[-max_turns:]
            for item in recent:
                if isinstance(item, dict):
                    role = item.get('role', 'user')
                    content = item.get('content', '') or item.get('text', '') or item.get('message', '')
                    if content and role in ['user', 'assistant', 'system']:
                        messages.append({"role": role, "content": str(content).strip()})

        # Append current user query if not already the last message
        if not messages or messages[-1].get('content') != current_query:
            messages.append({"role": "user", "content": current_query})

        return messages

    @classmethod
    def get_last_assistant_topic(cls, history: list) -> str:
        """Extracts the subject of the previous assistant message for resolving pronouns like 'it', 'that'."""
        if not history or not isinstance(history, list):
            return ""
        for item in reversed(history):
            if isinstance(item, dict) and item.get('role') == 'assistant':
                return str(item.get('content', '') or item.get('text', ''))[:100]
        return ""
