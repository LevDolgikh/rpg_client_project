from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_SETTINGS: dict[str, Any] = {
    "temperature": 0.7,
    "top_p": 0.9,
    "presence_penalty": 0.3,
    "frequency_penalty": 0.2,
    "max_tokens": 120,
    "prompt_debug": False,
}


@dataclass
class GameState:
    player_name: str = "Player"
    character_name: str = "Character"
    player_description: str = ""
    character_description: str = ""
    character_goal: str = ""
    world_scenario: str = ""
    story_direction: str = ""
    scene_memory: str = ""
    chat_history: list[tuple[str, str]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_name": self.player_name,
            "character_name": self.character_name,
            "player_description": self.player_description,
            "character_description": self.character_description,
            "character_goal": self.character_goal,
            "world_scenario": self.world_scenario,
            "story_direction": self.story_direction,
            "scene_memory": self.scene_memory,
            "chat_history": [list(message) for message in self.chat_history],
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        player_name = str(data.get("player_name", "Player"))
        character_name = str(data.get("character_name", "Character"))
        raw_history = data.get("chat_history", [])
        chat_history: list[tuple[str, str]] = []

        for item in raw_history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                speaker, text = item
                speaker_text = str(speaker).strip()
                message_text = cls._normalize_loaded_turn_text(
                    speaker=speaker_text,
                    text=str(text),
                    player_name=player_name,
                    character_name=character_name,
                )
                if speaker_text and message_text:
                    chat_history.append((speaker_text, message_text))

        settings = data.get("settings", {})
        if not isinstance(settings, dict):
            settings = {}
        merged_settings = dict(DEFAULT_SETTINGS)
        merged_settings.update(settings)

        return cls(
            player_name=player_name,
            character_name=character_name,
            player_description=str(data.get("player_description", "")),
            character_description=str(data.get("character_description", "")),
            character_goal=str(data.get("character_goal", "")),
            world_scenario=str(data.get("world_scenario", "")),
            story_direction=str(data.get("story_direction", "")),
            scene_memory=str(data.get("scene_memory", "")),
            chat_history=chat_history,
            settings=merged_settings,
        )

    @staticmethod
    def _normalize_loaded_turn_text(
        speaker: str,
        text: str,
        player_name: str,
        character_name: str,
    ) -> str:
        message = str(text).strip()
        if not message:
            return ""

        labels = {
            speaker,
            "Player",
            "Character",
            str(player_name).strip(),
            str(character_name).strip(),
        }

        for label in labels:
            normalized_label = str(label).strip()
            if not normalized_label:
                continue
            prefix = f"{normalized_label}:"
            if message.lower().startswith(prefix.lower()):
                message = message[len(prefix) :].lstrip()

        return message
