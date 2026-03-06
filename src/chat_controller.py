from __future__ import annotations

import logging
from typing import Callable

from context_builder import ContextBuilder
from llm_client import LLMClient, LLMClientError
from memory_manager import MemoryManager
from models import DEFAULT_SETTINGS, GameState
from prompts import ENHANCE_PROMPT

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
        llm_client: LLMClient,
        memory_manager: MemoryManager,
    ) -> None:
        self.state = state
        self.context_builder = context_builder
        self.llm_client = llm_client
        self.memory_manager = memory_manager

    def send_message(self, speaker: str, message: str) -> tuple[str, str] | None:
        """Add a user-authored message to chat history."""
        clean_speaker = str(speaker).strip()
        clean_message = self._normalize_turn_text(clean_speaker, str(message))

        if not clean_speaker or not clean_message:
            return None

        turn = (clean_speaker, clean_message)
        self.state.chat_history.append(turn)
        return turn

    def get_chat_history_text(self) -> str:
        return "\n\n".join(f"{speaker}: {text}" for speaker, text in self.state.chat_history)

    def delete_last_message(self) -> tuple[str, str] | None:
        """Delete and return the latest chat turn, if present."""
        if not self.state.chat_history:
            return None
        return self.state.chat_history.pop()

    def generate_response(
        self,
        speaker: str,
        user_input: str = "",
        stream: bool = False,
        on_stream_token: Callable[[str], None] | None = None,
    ) -> str:
        """Generate a response for the selected speaker and store it in history."""
        next_speaker = str(speaker).strip()
        if not next_speaker:
            raise ValueError("speaker is required")

        messages = self.context_builder.build_messages(
            state=self.state,
            next_speaker=next_speaker,
            user_input=user_input,
            response_reserve_tokens=self._get_max_tokens(),
        )

        params = self._generation_params()

        try:
            if stream:
                chunks: list[str] = []
                for chunk in self.llm_client.generate_stream(messages, **params):
                    chunks.append(chunk)
                    if on_stream_token is not None:
                        on_stream_token(chunk)
                response_text = "".join(chunks).strip()
            else:
                response_text = self.llm_client.generate(messages, **params)
        except LLMClientError:
            logger.exception("Generation failed for speaker '%s'.", next_speaker)
            raise

        normalized_response = self._normalize_turn_text(next_speaker, response_text)
        if normalized_response:
            self.state.chat_history.append((next_speaker, normalized_response))

        return normalized_response

    def enhance_message(self, speaker: str, message: str) -> str:
        """Rewrite a message in richer roleplay style."""
        clean_speaker = str(speaker).strip() or "Player"
        original = self._normalize_turn_text(clean_speaker, str(message))
        if not original:
            return ""

        trimmed_history = self.context_builder.trim_history(
            state=self.state,
            next_speaker=clean_speaker,
            user_input=original,
            response_reserve_tokens=self._get_max_tokens(),
        )
        history_text = "\n".join(f"{turn_speaker}: {turn_text}" for turn_speaker, turn_text in trimmed_history)
        context_block = self.context_builder.build_context_block(self.state)

        prompt = ENHANCE_PROMPT.format(
            speaker=clean_speaker,
            context_block=context_block,
            chat_history=history_text if history_text else "(no chat history)",
            user_message=original,
        )
        messages = [{"role": "user", "content": prompt}]

        try:
            return self.llm_client.generate(messages, **self._generation_params()).strip()
        except LLMClientError:
            logger.exception("Enhance message request failed.")
            raise

    def redo_response(
        self,
        stream: bool = False,
        on_stream_token: Callable[[str], None] | None = None,
    ) -> str:
        """
        Generate an alternative version of the last response.

        Removes the latest chat turn and regenerates for the same speaker.
        """
        if not self.state.chat_history:
            return ""

        last_speaker, _last_text = self.state.chat_history.pop()
        return self.generate_response(
            speaker=last_speaker,
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
            append_scene_memory=False,
        )
        return summary

    def stop_generation(self) -> None:
        """Stop active streaming generation."""
        self.llm_client.cancel_generation()

    def is_server_connected(self) -> bool:
        return self.llm_client.is_available()

    def get_memory_limit(self) -> int:
        return self.context_builder.token_manager.max_tokens

    def set_memory_limit(self, limit: int) -> None:
        self.context_builder.token_manager.set_max_tokens(limit)

    def estimate_text_tokens(self, text: str) -> int:
        return self.context_builder.token_manager.estimate_tokens(text)

    def preview_context_tokens(self, next_speaker: str, user_input: str = "") -> tuple[int, int]:
        messages = self.context_builder.build_messages(
            state=self.state,
            next_speaker=next_speaker,
            user_input=user_input,
            response_reserve_tokens=self.get_max_tokens(),
        )
        used = self.context_builder.token_manager.count_tokens(messages=messages)
        return used, self.context_builder.token_manager.max_tokens

    def apply_generation_settings(
        self,
        temperature: float,
        top_p: float,
        presence_penalty: float,
        frequency_penalty: float,
        max_tokens: int,
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
        self.state.settings["max_tokens"] = max(1, int(max_tokens))
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
            "max_tokens": self._get_max_tokens(),
        }

    def _get_max_tokens(self) -> int:
        value = self.state.settings.get("max_tokens", DEFAULT_SETTINGS["max_tokens"])
        try:
            max_tokens = int(value)
        except (TypeError, ValueError):
            return int(DEFAULT_SETTINGS["max_tokens"])
        return max(1, max_tokens)

    def get_max_tokens(self) -> int:
        return self._get_max_tokens()

    def _clamp_float(self, value: float, min_value: float, max_value: float) -> float:
        parsed = float(value)
        if parsed < min_value:
            return min_value
        if parsed > max_value:
            return max_value
        return parsed

    def _normalize_turn_text(self, speaker: str, text: str) -> str:
        message = str(text).strip()
        if not message:
            return ""

        candidates = {
            str(speaker).strip(),
            "Player",
            "Character",
            self.state.player_name,
            self.state.character_name,
        }
        for label in candidates:
            normalized_label = str(label).strip()
            if not normalized_label:
                continue
            prefix = f"{normalized_label}:"
            if message.lower().startswith(prefix.lower()):
                message = message[len(prefix) :].lstrip()

        return message
