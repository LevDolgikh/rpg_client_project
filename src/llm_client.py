"""Low-level client for OpenAI-compatible LLM servers."""

from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI


logger = logging.getLogger(__name__)


class LLMClientError(RuntimeError):
    """Raised when a request to the LLM client cannot be completed."""


class LLMClient:
    """Thin wrapper over OpenAI-compatible Responses API."""

    def __init__(self) -> None:
        self._client: OpenAI | None = None
        self._current_model: str | None = None
        self._model_ids: list[str] = []

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def current_model(self) -> str:
        return self._current_model or ""

    @property
    def model_ids(self) -> list[str]:
        return list(self._model_ids)

    def connect(self, base_url: str, api_key: str) -> list[str]:
        """Connect to server and return available model IDs."""
        if not base_url:
            raise LLMClientError("Server URL is required.")

        try:
            self._client = OpenAI(base_url=base_url, api_key=api_key)
            models = self._client.models.list().data
        except Exception as exc:
            self.disconnect()
            logger.exception("Failed to connect to LLM server: %s", base_url)
            raise LLMClientError(f"Failed to connect to server: {exc}") from exc

        self._model_ids = [model.id for model in models if getattr(model, "id", None)]
        if not self._model_ids:
            self.disconnect()
            raise LLMClientError("Connected, but no models were returned by server.")

        self._current_model = self._model_ids[0]
        return self.model_ids

    def disconnect(self) -> None:
        """Close active connection and clear state."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                logger.exception("Failed to close LLM client cleanly.")
        self._client = None
        self._current_model = None
        self._model_ids = []

    def set_model(self, model_id: str) -> None:
        """Set model for subsequent requests."""
        if not self.is_connected:
            raise LLMClientError("Client is not connected.")
        if model_id not in self._model_ids:
            raise LLMClientError(f"Model '{model_id}' is not available.")
        self._current_model = model_id

    def generate_response(self, instructions: str, user_input: Any) -> str:
        """Generate a non-streaming text response from the active model."""
        if not self.is_connected:
            raise LLMClientError("Client is not connected.")
        if not self._current_model:
            raise LLMClientError("No active model selected.")
        if user_input is None or (isinstance(user_input, str) and not user_input.strip()):
            raise LLMClientError("Input message is empty.")

        try:
            response = self._client.responses.create(
                model=self._current_model,
                instructions=instructions,
                input=user_input,
                stream=False,
            )
        except Exception as exc:
            logger.exception("LLM response generation failed.")
            raise LLMClientError(f"Response generation failed: {exc}") from exc

        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise LLMClientError("Server returned an empty response.")
        return output_text
