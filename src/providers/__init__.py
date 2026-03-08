from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator, List

import json
import requests

from llm_client import LLMClient, LLMClientError, DEFAULT_BASE_URL


class LLMProvider(ABC):
    """Abstract interface for all LLM providers.

    The rest of the application interacts solely through this interface.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Validate configuration and check that the provider is reachable.

        Returns `True` if the connection succeeded/appears healthy.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Perform any cleanup related to an active connection."""

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return a list of available model names for the provider."""

    @abstractmethod
    def generate(
        self, messages: list[dict[str, str]], **kwargs
    ) -> str:
        """Generate a full (non-streaming) response from the provider."""

    @abstractmethod
    def generate_stream(
        self, messages: list[dict[str, str]], **kwargs
    ) -> Iterator[str]:
        """Stream response chunks from the provider."""

    # Optional helpers that concrete implementations may provide
    @property
    def base_url(self) -> str:
        raise NotImplementedError

    @property
    def model(self) -> str:
        raise NotImplementedError

    def cancel_generation(self) -> None:
        """Signal a streaming generation to stop (if supported)."""
        # Default no-op
        pass

    def is_available(self) -> bool:
        """Return whether the provider is currently reachable.

        This is used by the UI to determine connection status.
        """
        return False


class LocalProvider(LLMProvider):
    """Wrapper around the existing `LLMClient` for local servers.

    This provider implements the basic OpenAI-style API used by LM Studio or
    a locally hosted Ollama server. It is intended to be a thin adapter that
    forwards calls to `LLMClient` while satisfying the provider interface.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = "local-model",
        timeout: int = 60,
    ) -> None:
        self._client = LLMClient(base_url=base_url, model=model, timeout=timeout)

    # ---- interface implementation ----
    def connect(self) -> bool:
        # For a local provider the best we can do is check availability.
        return self._client.is_available()

    def disconnect(self) -> None:
        # No persistent connection to close for local clients.
        pass

    def list_models(self) -> List[str]:
        try:
            response = self._client._session.get(
                f"{self._client.base_url}/v1/models", timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
        except Exception as exc:  # keep safe boundaries
            raise LLMClientError("Failed to list models") from exc

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:  # type: ignore[override]
        return self._client.generate(messages, **kwargs)

    def generate_stream(
        self, messages: list[dict[str, str]], **kwargs
    ) -> Iterator[str]:
        return self._client.generate_stream(messages, **kwargs)

    # ---- helpers forwarded from LLMClient ----
    @property
    def base_url(self) -> str:
        return self._client.base_url

    @property
    def model(self) -> str:
        return self._client.model

    def cancel_generation(self) -> None:
        self._client.cancel_generation()

    def is_available(self) -> bool:
        return self._client.is_available()

    # allow external configuration if UI wants to update
    def set_base_url(self, url: str) -> None:
        self._client.set_base_url(url)

    def set_model(self, model: str) -> None:
        self._client.model = model


# stub classes for future providers
class OpenAIProvider(LLMProvider):
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com",
        model: str = "",
        timeout: int = 60,
    ):
        self.api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self.timeout = timeout
        self._session = requests.Session()
        self._cancel_requested = False

    def connect(self) -> bool:
        # perform a simple availability check using model list endpoint
        if not self.api_key:
            return False
        try:
            resp = self._session.get(
                f"{self._base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
            )
            return resp.ok
        except requests.RequestException:
            return False

    def is_available(self) -> bool:
        return self.connect()

    def cancel_generation(self) -> None:
        self._cancel_requested = True

    def disconnect(self) -> None:
        # nothing to cleanup for stateless HTTP provider
        pass

    def list_models(self) -> List[str]:
        try:
            resp = self._session.get(
                f"{self._base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
        except Exception as exc:
            raise LLMClientError("Failed to list OpenAI models") from exc

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:  # type: ignore[override]
        payload = {
            "model": self._model,
            "messages": messages,
            **({k: v for k, v in kwargs.items() if v is not None}),
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self._session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("OpenAI request failed.")
            raise LLMClientError(f"Request failed: {exc}") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.exception("Invalid OpenAI response payload.")
            raise LLMClientError("Invalid response format from OpenAI API.") from exc

    def generate_stream(
        self, messages: list[dict[str, str]], **kwargs
    ) -> Iterator[str]:
        self._cancel_requested = False
        payload = {
            "model": self._model,
            "messages": messages,
            **({k: v for k, v in kwargs.items() if v is not None}),
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self._session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("OpenAI streaming request failed.")
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
                # reuse LLMClient extraction logic
                delta = OpenAIProvider._extract_delta_text(payload_item)
                if delta:
                    yield delta
        finally:
            response.close()

    @staticmethod
    def _extract_delta_text(payload: dict) -> str:
        try:
            choice = payload["choices"][0]
        except (KeyError, IndexError, TypeError):
            return ""
        delta = choice.get("delta")
        if isinstance(delta, dict):
            return str(delta.get("content", ""))
        message = choice.get("message")
        if isinstance(message, dict):
            return str(message.get("content", ""))
        return str(choice.get("text", ""))

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def model(self) -> str:
        return self._model

    def set_model(self, model: str) -> None:
        self._model = model

    def set_base_url(self, url: str) -> None:
        self._base_url = str(url).strip().rstrip("/")

    def set_api_key(self, key: str) -> None:
        self.api_key = key
    

class OllamaCloudProvider(LLMProvider):
    def __init__(self, api_key: str = "", base_url: str = "https://api.ollama.com", model: str = "", timeout: int = 60):
        self.api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self.timeout = timeout
        self._session = requests.Session()
        self._cancel_requested = False

    def connect(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self._session.get(
                f"{self._base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
            )
            return resp.ok
        except requests.RequestException:
            return False

    def is_available(self) -> bool:
        return self.connect()

    def cancel_generation(self) -> None:
        self._cancel_requested = True

    def disconnect(self) -> None:
        pass

    def list_models(self) -> List[str]:
        try:
            resp = self._session.get(
                f"{self._base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return [m.get("id", "") for m in data.get("data", []) if isinstance(m, dict)]
        except Exception as exc:
            raise LLMClientError("Failed to list Ollama Cloud models") from exc

    def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        payload = {
            "model": self._model,
            "messages": messages,
            **({k: v for k, v in kwargs.items() if v is not None}),
            "stream": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self._session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Ollama Cloud request failed.")
            raise LLMClientError(f"Request failed: {exc}") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.exception("Invalid Ollama Cloud response payload.")
            raise LLMClientError("Invalid response format from Ollama Cloud API.") from exc

    def generate_stream(self, messages: list[dict[str, str]], **kwargs) -> Iterator[str]:
        self._cancel_requested = False
        payload = {
            "model": self._model,
            "messages": messages,
            **({k: v for k, v in kwargs.items() if v is not None}),
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self._session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("Ollama Cloud streaming request failed.")
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
                delta = OpenAIProvider._extract_delta_text(payload_item)
                if delta:
                    yield delta
        finally:
            response.close()

    def set_base_url(self, url: str) -> None:
        self._base_url = str(url).strip().rstrip("/")

    def set_model(self, model: str) -> None:
        self._model = model

    def set_api_key(self, key: str) -> None:
        self.api_key = key


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Factory returning a provider instance by name."""
    name = provider_name.lower()
    if name == "local":
        return LocalProvider(**kwargs)
    if name == "openai":
        return OpenAIProvider(**kwargs)
    if name in ("ollama_cloud", "ollamacloud"):
        return OllamaCloudProvider(**kwargs)
    raise ValueError(f"Unknown provider '{provider_name}'")
