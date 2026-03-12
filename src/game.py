"""Application-level RPG client service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from llm_client import LLMClient, LLMClientError
from settings import AppSettings


@dataclass
class OperationResult:
    """Unified result object for UI-safe error handling."""

    ok: bool
    value: Any = None
    error: str = ""


class RPGClient:
    """Coordinates game context with the low-level LLM client."""

    _ESTIMATED_CHARS_PER_TOKEN = 4

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def connect_to_llm(self, base_url: str, api_key: str) -> OperationResult:
        try:
            model_ids = self.llm_client.connect(base_url=base_url, api_key=api_key)
            return OperationResult(ok=True, value=model_ids)
        except LLMClientError as exc:
            return OperationResult(ok=False, error=str(exc))

    def disconnect_from_llm(self) -> None:
        self.llm_client.disconnect()

    def set_active_model(self, model_id: str) -> OperationResult:
        try:
            self.llm_client.set_model(model_id)
            return OperationResult(ok=True)
        except LLMClientError as exc:
            return OperationResult(ok=False, error=str(exc))

    def generate_response(
        self,
        character_name: str,
        character_description: str,
        world_description: str,
        message_history: str,
        token_limit: int,
    ) -> OperationResult:
        if not character_name.strip():
            return OperationResult(ok=False, error="Character name is required.")
        if not message_history.strip():
            return OperationResult(ok=False, error="Message history is empty.")

        system_prompt = self._build_system_prompt(
            character_name=character_name,
            character_description=character_description,
            world_description=world_description,
        )
        system_prompt, message_history = self._trim_context_by_token_limit(
            system_prompt=system_prompt,
            message_history=message_history,
            token_limit=token_limit,
        )
        if not message_history.strip():
            return OperationResult(
                ok=False,
                error="Token limit is too low for message history.",
            )

        try:
            response_text = self.llm_client.generate_response(
                instructions=system_prompt,
                user_input=message_history,
            )
            return OperationResult(ok=True, value=response_text)
        except LLMClientError as exc:
            return OperationResult(ok=False, error=str(exc))

    def generate_response_stream(
        self,
        character_name: str,
        character_description: str,
        world_description: str,
        message_history: str,
        token_limit: int,
        on_chunk: Callable[[str], None],
    ) -> OperationResult:
        if not character_name.strip():
            return OperationResult(ok=False, error="Character name is required.")
        if not message_history.strip():
            return OperationResult(ok=False, error="Message history is empty.")

        system_prompt = self._build_system_prompt(
            character_name=character_name,
            character_description=character_description,
            world_description=world_description,
        )
        system_prompt, message_history = self._trim_context_by_token_limit(
            system_prompt=system_prompt,
            message_history=message_history,
            token_limit=token_limit,
        )
        if not message_history.strip():
            return OperationResult(
                ok=False,
                error="Token limit is too low for message history.",
            )

        try:
            self.llm_client.generate_response_stream(
                instructions=system_prompt,
                user_input=message_history,
                on_chunk=on_chunk,
            )
            return OperationResult(ok=True)
        except LLMClientError as exc:
            return OperationResult(ok=False, error=str(exc))

    @staticmethod
    def _build_system_prompt(
        character_name: str,
        character_description: str,
        world_description: str,
    ) -> str:
        role_prompt = AppSettings.SYSTEM_PROMPT.format(character_name=character_name)
        context_prompt = AppSettings.CONTEXT_TEMPLATE.format(
            character_name=character_name,
            character_description=character_description,
            world_description=world_description,
        )
        return f"{role_prompt}\n{context_prompt}".strip()

    @classmethod
    def _estimate_tokens(cls, text: str) -> int:
        normalized = text.strip()
        if not normalized:
            return 0
        return max(1, (len(normalized) + cls._ESTIMATED_CHARS_PER_TOKEN - 1) // cls._ESTIMATED_CHARS_PER_TOKEN)

    @classmethod
    def _trim_text_to_token_budget(cls, text: str, token_budget: int) -> str:
        if token_budget < 1:
            return ""
        max_chars = token_budget * cls._ESTIMATED_CHARS_PER_TOKEN
        return text[-max_chars:].strip()

    @classmethod
    def _trim_context_by_token_limit(
        cls,
        system_prompt: str,
        message_history: str,
        token_limit: int,
    ) -> tuple[str, str]:
        normalized_limit = max(1, int(token_limit))
        system_tokens = cls._estimate_tokens(system_prompt)

        if system_tokens >= normalized_limit:
            trimmed_system = cls._trim_text_to_token_budget(system_prompt, normalized_limit)
            return trimmed_system, ""

        remaining_tokens = normalized_limit - system_tokens
        message_blocks = [block.strip() for block in message_history.split("\n\n") if block.strip()]
        if not message_blocks:
            return system_prompt, ""

        selected_blocks: list[str] = []
        used_tokens = 0
        for block in reversed(message_blocks):
            block_tokens = cls._estimate_tokens(block)
            if used_tokens + block_tokens <= remaining_tokens:
                selected_blocks.append(block)
                used_tokens += block_tokens
                continue

            if not selected_blocks:
                partial_block = cls._trim_text_to_token_budget(block, remaining_tokens)
                if partial_block:
                    selected_blocks.append(partial_block)
            break

        selected_blocks.reverse()
        return system_prompt, "\n\n".join(selected_blocks)
