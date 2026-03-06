from __future__ import annotations

import json
import logging
from typing import Iterator

import requests

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when LM Studio request/response handling fails."""


class LLMClient:
    """OpenAI-compatible client for LM Studio chat completions."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:1234",
        model: str = "local-model",
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._session = requests.Session()
        self._cancel_requested = False

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def cancel_generation(self) -> None:
        """Signal active streaming generation to stop."""
        self._cancel_requested = True

    def is_available(self) -> bool:
        """Check whether LM Studio API is reachable."""
        try:
            response = self._session.get(f"{self.base_url}/v1/models", timeout=5)
            return response.ok
        except requests.RequestException:
            return False

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a full response (non-streaming)."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        logger.info("Sending non-stream request to LM Studio.")
        try:
            response = self._session.post(
                self.chat_completions_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("LM Studio request failed.")
            raise LLMClientError(f"Request failed: {exc}") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.exception("Invalid LM Studio response payload.")
            raise LLMClientError("Invalid response format from LM Studio.") from exc

    def generate_stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Stream response chunks from LM Studio.

        Yields incremental text tokens/chunks as they arrive.
        """
        self._cancel_requested = False

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        logger.info("Sending stream request to LM Studio.")
        try:
            response = self._session.post(
                self.chat_completions_url,
                json=payload,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("LM Studio streaming request failed.")
            raise LLMClientError(f"Streaming request failed: {exc}") from exc

        try:
            for raw_line in response.iter_lines(decode_unicode=True):
                if self._cancel_requested:
                    logger.info("Streaming generation cancelled by user.")
                    break

                if not raw_line:
                    continue

                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue

                data_str = line[len("data:") :].strip()
                if data_str == "[DONE]":
                    break

                try:
                    payload_item = json.loads(data_str)
                except json.JSONDecodeError:
                    logger.debug("Skipping non-JSON stream payload: %s", data_str)
                    continue

                delta = self._extract_delta_text(payload_item)
                if delta:
                    yield delta
        finally:
            response.close()

    def _extract_delta_text(self, payload: dict) -> str:
        """Extract streamed text from OpenAI-compatible delta payload."""
        try:
            choice = payload["choices"][0]
        except (KeyError, IndexError, TypeError):
            return ""

        delta = choice.get("delta")
        if isinstance(delta, dict):
            content = delta.get("content", "")
            return str(content)

        # Some servers may send full message fragments in streaming mode.
        message = choice.get("message")
        if isinstance(message, dict):
            content = message.get("content", "")
            return str(content)

        text = choice.get("text", "")
        return str(text)
