from __future__ import annotations

from models import GameState
from prompts import CONTEXT_TEMPLATE, SYSTEM_PROMPT
from token_manager import TokenManager


class ContextBuilder:
    """Builds structured LLM messages from the current game state."""

    def __init__(self, token_manager: TokenManager, max_chat_messages: int = 16) -> None:
        self.token_manager = token_manager
        self.max_chat_messages = max_chat_messages

    def build_messages(
        self,
        state: GameState,
        user_input: str = "",
        response_reserve_tokens: int = 150,
    ) -> list[dict[str, str]]:
        """
        Assemble messages in strict order:
        1) system prompt
        2) context block
        3) recent chat history
        4) current player input (optional)
        """
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self._build_system_prompt(state),
            },
            {
                "role": "user",
                "content": self.build_context_block(state),
            },
        ]

        history = self.trim_history(
            state=state,
            user_input=user_input,
            response_reserve_tokens=response_reserve_tokens,
        )
        messages.extend(self.build_chat_history(history))

        clean_input = GameState._normalize_turn_text(
            text=user_input,
            player_name=state.player_name,
            character_name=state.character_name,
        )
        if clean_input:
            messages.append({"role": "user", "content": clean_input})

        return messages

    def build_context_block(self, state: GameState) -> str:
        """Build the context block exactly from the context template."""
        return CONTEXT_TEMPLATE.format(
            character_description=state.character_description.strip(),
            player_description=state.player_description.strip(),
            story_intent=state.story_intent.strip(),
            world_scenario=state.world_scenario.strip(),
            scene_memory=state.scene_memory.strip(),
        )

    def build_chat_history(self, chat_history: list[dict[str, str]]) -> list[dict[str, str]]:
        """Convert canonical chat turns into OpenAI-compatible role messages."""
        messages: list[dict[str, str]] = []

        for turn in chat_history:
            if not isinstance(turn, dict):
                continue

            speaker = GameState._normalize_speaker(turn.get("speaker", ""))
            message_text = GameState._normalize_turn_text(
                text=turn.get("text", ""),
                player_name="",
                character_name="",
            )
            if not speaker or not message_text:
                continue

            messages.append(
                {
                    "role": self._speaker_to_role(speaker),
                    "content": message_text,
                }
            )

        return messages

    def trim_history(
        self,
        state: GameState,
        user_input: str = "",
        response_reserve_tokens: int = 150,
    ) -> list[dict[str, str]]:
        """Trim oldest chat messages first until token budget fits."""
        history = list(state.chat_history)
        if self.max_chat_messages > 0 and len(history) > self.max_chat_messages:
            history = history[-self.max_chat_messages :]

        while history:
            candidate_messages = self._build_candidate_messages(
                state=state,
                history=history,
                user_input=user_input,
            )
            token_count = self.token_manager.count_tokens(messages=candidate_messages)
            if self.token_manager.check_limit(
                token_count,
                reserve_tokens=response_reserve_tokens,
            ):
                return history

            history.pop(0)

        return []

    def _build_candidate_messages(
        self,
        state: GameState,
        history: list[dict[str, str]],
        user_input: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self._build_system_prompt(state),
            },
            {
                "role": "user",
                "content": self.build_context_block(state),
            },
        ]
        messages.extend(self.build_chat_history(history))

        clean_input = GameState._normalize_turn_text(
            text=user_input,
            player_name=state.player_name,
            character_name=state.character_name,
        )
        if clean_input:
            messages.append({"role": "user", "content": clean_input})

        return messages

    def _speaker_to_role(self, speaker: str) -> str:
        if speaker == "player":
            return "user"
        if speaker == "character":
            return "assistant"
        raise ValueError(f"Unsupported speaker value: {speaker}")

    def _build_system_prompt(self, state: GameState) -> str:
        active_name = state.character_name.strip() or "Character"
        return SYSTEM_PROMPT.format(character_name=active_name)
