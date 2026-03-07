from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "temperature": 0.7,
    "top_p": 0.9,
    "presence_penalty": 0.3,
    "frequency_penalty": 0.2,
    "context_limit": 4096,
    "llm_base_url": "http://127.0.0.1:1234",
    "prompt_debug": False,
}


@dataclass
class GameState:
    player_name: str = "Player"
    character_name: str = "Character"
    player_description: str = ""
    character_description: str = ""
    story_intent: str = ""
    world_scenario: str = ""
    scene_memory: str = ""
    chat_history: list[dict[str, str]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))

    def to_dict(self) -> dict[str, Any]:
        settings_payload = dict(DEFAULT_SETTINGS)
        for key in DEFAULT_SETTINGS:
            if key in self.settings:
                settings_payload[key] = self.settings[key]

        canonical_history: list[dict[str, str]] = []
        for turn in self.chat_history:
            if not isinstance(turn, dict):
                continue
            speaker = self._normalize_speaker(turn.get("speaker", ""))
            text = self._normalize_turn_text(
                text=turn.get("text", ""),
                player_name=self.player_name,
                character_name=self.character_name,
            )
            if speaker and text:
                canonical_history.append({"speaker": speaker, "text": text})

        return {
            "version": 2,
            "player_name": self.player_name,
            "character_name": self.character_name,
            "player_description": self.player_description,
            "character_description": self.character_description,
            "story_intent": self.story_intent,
            "world_scenario": self.world_scenario,
            "scene_memory": self.scene_memory,
            "chat_history": canonical_history,
            "settings": settings_payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        if not isinstance(data, dict):
            raise ValueError("Save file must be a JSON object.")

        version = data.get("version")
        if version != 2:
            raise ValueError("Unsupported save version. Expected version 2.")

        player_name = str(data.get("player_name", "Player"))
        character_name = str(data.get("character_name", "Character"))

        raw_history = data.get("chat_history", [])
        if not isinstance(raw_history, list):
            raise ValueError("Invalid chat history: expected an array of turns.")

        chat_history: list[dict[str, str]] = []
        for idx, item in enumerate(raw_history):
            if not isinstance(item, dict):
                raise ValueError(f"Invalid chat turn at index {idx}: expected object.")

            speaker = cls._normalize_speaker(item.get("speaker", ""))
            if not speaker:
                raise ValueError(
                    f"Invalid speaker at chat turn {idx}. Allowed: 'player', 'character'."
                )

            text = cls._normalize_turn_text(
                text=item.get("text", ""),
                player_name=player_name,
                character_name=character_name,
            )
            if not text:
                raise ValueError(f"Invalid chat turn text at index {idx}: text is empty.")

            chat_history.append({"speaker": speaker, "text": text})

        settings = data.get("settings", {})
        if not isinstance(settings, dict):
            settings = {}

        merged_settings = dict(DEFAULT_SETTINGS)
        for key in DEFAULT_SETTINGS:
            if key in settings:
                merged_settings[key] = settings[key]

        return cls(
            player_name=player_name,
            character_name=character_name,
            player_description=str(data.get("player_description", "")),
            character_description=str(data.get("character_description", "")),
            story_intent=str(data.get("story_intent", "")),
            world_scenario=str(data.get("world_scenario", "")),
            scene_memory=str(data.get("scene_memory", "")),
            chat_history=chat_history,
            settings=merged_settings,
        )

    @staticmethod
    def _normalize_speaker(value: Any) -> str:
        speaker = str(value).strip().lower()
        if speaker == "player":
            return "player"
        if speaker == "character":
            return "character"
        return ""

    @staticmethod
    def _normalize_turn_text(text: Any, player_name: str, character_name: str) -> str:
        message = str(text).strip()
        if not message:
            return ""

        labels = [
            "Player",
            "Character",
            "player",
            "character",
            str(player_name).strip(),
            str(character_name).strip(),
        ]

        for label in labels:
            normalized_label = str(label).strip()
            if not normalized_label:
                continue
            prefix = f"{normalized_label}:"
            if message.lower().startswith(prefix.lower()):
                message = message[len(prefix) :].lstrip()
                break

        return message
