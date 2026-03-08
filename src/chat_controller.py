from __future__ import annotations

import logging
import re
from typing import Callable

from context_builder import ContextBuilder
from memory_manager import MemoryManager
from models import DEFAULT_SETTINGS, GameState

# provider abstraction
from providers import LLMProvider
from llm_client import DEFAULT_BASE_URL, LLMClientError

logger = logging.getLogger(__name__)

TEMPERATURE_RANGE = (0.5, 0.9)
TOP_P_RANGE = (0.8, 0.95)
PRESENCE_PENALTY_RANGE = (0.0, 0.6)
FREQUENCY_PENALTY_RANGE = (0.0, 0.5)


class ChatController:
    """Coordinates UI actions, prompt building, and LLM calls."""

    def __init__(
        self,
        state: GameState,
        context_builder: ContextBuilder,
        provider: LLMProvider,
        memory_manager: MemoryManager,
    ) -> None:
        self.state = state
        self.context_builder = context_builder
        self.provider = provider
        self.memory_manager = memory_manager

    def send_player_message(self, message: str) -> dict[str, str] | None:
        """Add a player-authored message to chat history."""
        clean_message = GameState._normalize_turn_text(
            text=message,
            player_name=self.state.player_name,
            character_name=self.state.character_name,
        )
        if not clean_message:
            return None

        turn = {"speaker": "player", "text": clean_message}
        self.state.chat_history.append(turn)
        return turn

    def get_chat_history_text(self) -> str:
        lines: list[str] = []
        for turn in self.state.chat_history:
            if not isinstance(turn, dict):
                continue
            speaker = GameState._normalize_speaker(turn.get("speaker", ""))
            text = str(turn.get("text", "")).strip()
            if not speaker or not text:
                continue
            lines.append(f"{self._display_name_for_speaker(speaker)}: {text}")
        return "\n\n".join(lines)

    def delete_last_message(self) -> dict[str, str] | None:
        """Delete and return the latest chat turn, if present."""
        if not self.state.chat_history:
            return None
        return self.state.chat_history.pop()

    def generate_character_response(
        self,
        stream: bool = False,
        on_stream_token: Callable[[str], None] | None = None,
    ) -> str:
        """Generate a character response from current state and history."""
        messages = self.context_builder.build_messages(
            state=self.state,
            user_input="",
            response_reserve_tokens=0,
        )

        params = self._generation_params()

        try:
            if stream:
                chunks: list[str] = []
                for chunk in self.provider.generate_stream(messages, **params):
                    chunks.append(chunk)
                    if on_stream_token is not None:
                        on_stream_token(chunk)
                response_text = "".join(chunks)
            else:
                response_text = self.provider.generate(messages, **params)
        except LLMClientError:
            logger.exception("Character generation failed.")
            raise

        response_text = self.normalize_character_text(response_text)

        normalized_response = GameState._normalize_turn_text(
            text=response_text,
            player_name=self.state.player_name,
            character_name=self.state.character_name,
        )
        normalized_response = self.normalize_character_text(normalized_response)
        if normalized_response:
            self.state.chat_history.append({"speaker": "character", "text": normalized_response})

        return normalized_response

    def redo_response(
        self,
        stream: bool = False,
        on_stream_token: Callable[[str], None] | None = None,
    ) -> str:
        """Replace the latest character response with a new generation."""
        if not self.state.chat_history:
            return ""

        last_turn = self.state.chat_history[-1]
        if not isinstance(last_turn, dict):
            return ""

        last_speaker = GameState._normalize_speaker(last_turn.get("speaker", ""))
        if last_speaker != "character":
            return ""

        self.state.chat_history.pop()
        return self.generate_character_response(
            stream=stream,
            on_stream_token=on_stream_token,
        )

    def make_summary(self, messages_to_summarize: int | None = None) -> str:
        """Summarize older chat messages into scene memory."""
        if not self.state.chat_history:
            return ""

        if messages_to_summarize is None:
            messages_to_summarize = max(0, len(self.state.chat_history) // 2)

        summary = self.memory_manager.summarize_and_replace_history(
            state=self.state,
            messages_to_summarize=messages_to_summarize,
            append_scene_memory=True,
        )
        return summary

    def stop_generation(self) -> None:
        """Stop active streaming generation."""
        self.provider.cancel_generation()

    def is_server_connected(self) -> bool:
        return self.provider.is_available()

    # provider helper methods for UI and higher layers
    def connect(self) -> bool:
        """Attempt to connect/validate the active provider.

        Raises an exception if the underlying provider raises one or returns
        ``False`` indicating the connection failed. This allows callers to
        distinguish failure reasons and propagate messages to the user.
        """
        try:
            result = self.provider.connect()
            if not result:
                raise LLMClientError("Provider returned unavailable")
            return True
        except Exception as exc:
            logger.exception("Provider connection check failed.")
            # re-raise so UI can show specific message
            raise

    def disconnect(self) -> None:
        """Request provider to disconnect or cleanup."""
        try:
            self.provider.disconnect()
        except Exception:
            logger.exception("Provider disconnect failed.")

    def list_models(self) -> list[str]:
        try:
            return self.provider.list_models()
        except Exception as exc:
            logger.exception("Listing models failed.")
            # propagate error so UI can react
            raise

    def disconnect(self) -> None:
        """Request provider to disconnect or cleanup."""
        try:
            self.provider.disconnect()
        except Exception:
            logger.exception("Provider disconnect failed.")

    def list_models(self) -> list[str]:
        try:
            return self.provider.list_models()
        except Exception:
            logger.exception("Listing models failed.")
            return []

    def set_provider(self, new_provider: LLMProvider) -> None:
        """Swap the active provider implementation.

        Also updates dependent components (e.g. memory_manager).
        """
        self.provider = new_provider
        # make sure memory manager uses the same object for generation
        if hasattr(self, "memory_manager"):
            self.memory_manager.llm_client = new_provider

    def set_model(self, model: str) -> None:
        setter = getattr(self.provider, "set_model", None)
        if callable(setter):
            setter(model)

    def get_llm_base_url(self) -> str:
        # not all providers expose a base_url; fall back to empty string
        return getattr(self.provider, "base_url", "")

    def get_default_llm_base_url(self) -> str:
        return DEFAULT_BASE_URL

    def set_llm_base_url(self, base_url: str) -> str:
        normalized = str(base_url).strip().rstrip("/")
        if not normalized:
            normalized = DEFAULT_BASE_URL
        # delegate to provider if supported
        setter = getattr(self.provider, "set_base_url", None)
        if callable(setter):
            setter(normalized)
        return normalized

    def get_memory_limit(self) -> int:
        return self.context_builder.token_manager.max_tokens

    def set_memory_limit(self, limit: int) -> None:
        self.context_builder.token_manager.set_max_tokens(limit)

    def estimate_text_tokens(self, text: str) -> int:
        return self.context_builder.token_manager.estimate_tokens(text)

    @staticmethod
    def normalize_character_text(text: str) -> str:
        """Force model output into a single paragraph for display/history consistency."""
        collapsed_newlines = re.sub(r"[\r\n]+", " ", str(text))
        return re.sub(r"\s{2,}", " ", collapsed_newlines).strip()

    def preview_context_tokens(self, user_input: str = "") -> tuple[int, int]:
        messages = self.context_builder.build_preview_messages(
            state=self.state,
            user_input=user_input,
        )
        used = self.context_builder.token_manager.count_tokens(messages=messages)
        return used, self.context_builder.token_manager.max_tokens

    def apply_generation_settings(
        self,
        temperature: float,
        top_p: float,
        presence_penalty: float,
        frequency_penalty: float,
        prompt_debug: bool,
    ) -> None:
        self.state.settings["temperature"] = self._clamp_float(temperature, *TEMPERATURE_RANGE)
        self.state.settings["top_p"] = self._clamp_float(top_p, *TOP_P_RANGE)
        self.state.settings["presence_penalty"] = self._clamp_float(
            presence_penalty,
            *PRESENCE_PENALTY_RANGE,
        )
        self.state.settings["frequency_penalty"] = self._clamp_float(
            frequency_penalty,
            *FREQUENCY_PENALTY_RANGE,
        )
        self.state.settings["prompt_debug"] = bool(prompt_debug)

    def _generation_params(self) -> dict[str, float | int]:
        return {
            "temperature": float(self.state.settings.get("temperature", DEFAULT_SETTINGS["temperature"])),
            "top_p": float(self.state.settings.get("top_p", DEFAULT_SETTINGS["top_p"])),
            "presence_penalty": float(
                self.state.settings.get("presence_penalty", DEFAULT_SETTINGS["presence_penalty"])
            ),
            "frequency_penalty": float(
                self.state.settings.get("frequency_penalty", DEFAULT_SETTINGS["frequency_penalty"])
            ),
        }

    def _clamp_float(self, value: float, min_value: float, max_value: float) -> float:
        parsed = float(value)
        if parsed < min_value:
            return min_value
        if parsed > max_value:
            return max_value
        return parsed

    def _display_name_for_speaker(self, speaker: str) -> str:
        if speaker == "player":
            return self.state.player_name.strip() or "Player"
        if speaker == "character":
            return self.state.character_name.strip() or "Character"
        return speaker
