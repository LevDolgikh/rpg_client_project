from __future__ import annotations

from typing import Protocol

from models import GameState
from prompts import SUMMARY_PROMPT


class SupportsGenerate(Protocol):
    def generate(self, messages: list[dict[str, str]]) -> str:
        ...


class MemoryManager:
    """Handles manual chat summarization and scene memory updates."""

    def __init__(self, llm_client: SupportsGenerate) -> None:
        self.llm_client = llm_client

    def create_summary(self, chat_history: list[tuple[str, str]]) -> str:
        """Create a concise scene summary from chat history using the LLM."""
        if not chat_history:
            return ""

        prompt = SUMMARY_PROMPT.format(chat_history=self._format_chat_history(chat_history))
        messages = [{"role": "user", "content": prompt}]

        summary = self.llm_client.generate(messages)
        return summary.strip()

    def update_scene_memory(
        self,
        state: GameState,
        summary: str,
        append: bool = False,
    ) -> None:
        """Update scene memory with a new summary."""
        cleaned_summary = summary.strip()
        if not cleaned_summary:
            return

        if append and state.scene_memory.strip():
            state.scene_memory = f"{state.scene_memory.strip()}\n{cleaned_summary}"
        else:
            state.scene_memory = cleaned_summary

    def summarize_and_replace_history(
        self,
        state: GameState,
        messages_to_summarize: int,
        append_scene_memory: bool = False,
    ) -> str:
        """
        Summarize the oldest messages and remove them from chat history.

        This supports the documented flow where old chat is condensed into scene memory.
        """
        if messages_to_summarize <= 0 or not state.chat_history:
            return ""

        split_index = min(messages_to_summarize, len(state.chat_history))
        old_messages = state.chat_history[:split_index]
        summary = self.create_summary(old_messages)

        if not summary:
            return ""

        self.update_scene_memory(state, summary, append=append_scene_memory)
        state.chat_history = state.chat_history[split_index:]
        return summary

    def _format_chat_history(self, chat_history: list[tuple[str, str]]) -> str:
        lines: list[str] = []
        for speaker, text in chat_history:
            speaker_text = str(speaker).strip()
            message_text = str(text).strip()
            if not speaker_text or not message_text:
                continue
            lines.append(f"{speaker_text}: {message_text}")
        return "\n".join(lines)
