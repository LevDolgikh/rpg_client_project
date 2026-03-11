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
