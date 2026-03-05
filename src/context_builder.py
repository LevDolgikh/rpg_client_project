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
        next_speaker: str,
        user_input: str = "",
        response_reserve_tokens: int = 150,
    ) -> list[dict[str, str]]:
        """
        Assemble messages in the required order:
        1) system prompt
        2) context block
        3) recent chat history
        4) next speaker prefix
        """
        system_message = {
            "role": "system",
            "content": self._build_system_prompt(state, next_speaker),
        }

        context_message = {
            "role": "user",
            "content": self.build_context_block(state),
        }

        history = self.trim_history(
            state=state,
            next_speaker=next_speaker,
            user_input=user_input,
            response_reserve_tokens=response_reserve_tokens,
        )
        history_messages = self.build_chat_history(history)

        messages: list[dict[str, str]] = [system_message, context_message]
        messages.extend(history_messages)

        if user_input.strip():
            messages.append(
                {
                    "role": self._speaker_to_role(next_speaker),
                    "content": f"{next_speaker}: {user_input.strip()}",
                }
            )

        messages.append({"role": "user", "content": f"{next_speaker}:"})
        return messages

    def build_context_block(self, state: GameState) -> str:
        """Build the context block exactly from the context template."""
        return CONTEXT_TEMPLATE.format(
            character_description=state.character_description.strip(),
            player_description=state.player_description.strip(),
            character_goal=state.character_goal.strip(),
            world_scenario=state.world_scenario.strip(),
            story_direction=state.story_direction.strip(),
            scene_memory=state.scene_memory.strip(),
        )

    def build_chat_history(self, chat_history: list[tuple[str, str]]) -> list[dict[str, str]]:
        """Convert internal chat turns into OpenAI-compatible role messages."""
        messages: list[dict[str, str]] = []

        for speaker, text in chat_history:
            speaker_text = str(speaker).strip()
            message_text = str(text).strip()
            if not speaker_text or not message_text:
                continue

            messages.append(
                {
                    "role": self._speaker_to_role(speaker_text),
                    "content": f"{speaker_text}: {message_text}",
                }
            )

        return messages

    def trim_history(
        self,
        state: GameState,
        next_speaker: str,
        user_input: str = "",
        response_reserve_tokens: int = 150,
    ) -> list[tuple[str, str]]:
        """
        Trim oldest chat messages first until token budget fits.

        Preservation priority (from docs):
        - system prompt
        - context block
        - scene memory (inside context block)
        - recent chat history
        """
        history = list(state.chat_history)
        if self.max_chat_messages > 0 and len(history) > self.max_chat_messages:
            history = history[-self.max_chat_messages :]

        while history:
            candidate_messages = self._build_candidate_messages(
                state=state,
                history=history,
                next_speaker=next_speaker,
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
        history: list[tuple[str, str]],
        next_speaker: str,
        user_input: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self._build_system_prompt(state, next_speaker),
            },
            {
                "role": "user",
                "content": self.build_context_block(state),
            },
        ]
        messages.extend(self.build_chat_history(history))

        if user_input.strip():
            messages.append(
                {
                    "role": self._speaker_to_role(next_speaker),
                    "content": f"{next_speaker}: {user_input.strip()}",
                }
            )

        messages.append({"role": "user", "content": f"{next_speaker}:"})
        return messages

    def _speaker_to_role(self, speaker: str) -> str:
        normalized = speaker.strip().lower()
        if normalized == "character":
            return "assistant"
        return "user"

    def _build_system_prompt(self, state: GameState, next_speaker: str) -> str:
        normalized = str(next_speaker).strip().lower()
        if normalized == "player":
            active_name = state.player_name.strip() or "Player"
        else:
            active_name = state.character_name.strip() or "Character"
        return SYSTEM_PROMPT.format(character_name=active_name)

