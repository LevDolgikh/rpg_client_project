"""Tkinter GUI for the RPG chat client."""

from __future__ import annotations

import json
import logging
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

from game import OperationResult, RPGClient
from settings import AppSettings


logger = logging.getLogger(__name__)


class RPGUI(tk.Tk):
    """Main GUI window."""

    def __init__(self, rpg_client: RPGClient) -> None:
        super().__init__()
        self.rpg_client = rpg_client

        self.providers = AppSettings.BASE_CONNECTION_OPTIONS
        self.provider_names = [provider["name"] for provider in self.providers]
        self.default_provider = self.providers[0]
        self.default_provider_name = self.default_provider["name"]
        self.model_ids: list[str] = []

        self._build_layout()
        self._set_server_url_from_provider(self.default_provider_name)

    def _build_layout(self) -> None:
        self.title("RPG Chat Client")
        self.geometry("900x650")

        frame_global = tk.Frame(self)
        frame_global.pack(side="top", pady=20)

        frame_server = tk.LabelFrame(frame_global, text="Server Information")
        frame_server.grid(row=0, column=0, padx=5, pady=5, columnspan=3)

        tk.Label(frame_server, text="Provider:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        self.combobox_provider = ttk.Combobox(
            frame_server,
            values=self.provider_names,
            state="readonly",
        )
        self.combobox_provider.set(self.default_provider_name)
        self.combobox_provider.bind("<<ComboboxSelected>>", self.on_provider_selected)
        self.combobox_provider.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(frame_server, text="Presets").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )

        tk.Label(frame_server, text="Server URL:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_server_url = tk.Entry(frame_server, width=40)
        self.entry_server_url.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        tk.Label(
            frame_server,
            text="Example: https://api.openai.com/v1/ (OpenAI-compatible only)",
        ).grid(row=1, column=2, padx=5, pady=5, sticky="w")

        tk.Label(frame_server, text="API key:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_api_key = tk.Entry(frame_server, width=40, show="*")
        self.entry_api_key.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        tk.Label(frame_server, text="Leave blank for local models").grid(
            row=2, column=2, padx=5, pady=5, sticky="w"
        )

        frame_server_buttons = tk.Frame(frame_server)
        frame_server_buttons.grid(row=3, column=0, padx=5, pady=5, columnspan=3, sticky="w")

        self.button_connect = tk.Button(
            frame_server_buttons, text="Connect", command=self.connect, width=20
        )
        self.button_connect.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.button_disconnect = tk.Button(
            frame_server_buttons, text="Disconnect", command=self.disconnect, width=20
        )
        self.button_disconnect.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.label_connection = tk.Label(frame_server_buttons, text="Disconnected")
        self.label_connection.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        frame_world_character = tk.LabelFrame(
            frame_global, text="World and Character Settings", width=100
        )
        frame_world_character.grid(row=1, column=0, padx=5, pady=5, columnspan=3)

        tk.Label(frame_world_character, text="Model:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.combobox_model = ttk.Combobox(
            frame_world_character, values=self.model_ids, state="disabled"
        )
        self.combobox_model.bind("<<ComboboxSelected>>", self.on_model_selected)
        self.combobox_model.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tk.Label(frame_world_character, text="Character name:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_character_name = tk.Entry(frame_world_character)
        self.entry_character_name.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        tk.Label(frame_world_character, text="Player name:").grid(
            row=4, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_player_name = tk.Entry(frame_world_character)
        self.entry_player_name.grid(row=5, column=0, padx=5, pady=5, sticky="w")

        tk.Label(frame_world_character, text="World Information and Scenario").grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        self.text_world_description = tk.Text(frame_world_character, height=10, width=31)
        self.text_world_description.grid(
            row=1, column=1, padx=5, pady=5, sticky="w", rowspan=6
        )

        tk.Label(frame_world_character, text="Character Information").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.text_character_description = tk.Text(frame_world_character, height=10, width=31)
        self.text_character_description.grid(
            row=1, column=2, padx=5, pady=5, sticky="w", rowspan=6
        )

        frame_chat = tk.LabelFrame(frame_global, text="Chat")
        frame_chat.grid(row=2, column=0, padx=5, pady=5, columnspan=3)

        self.text_chat = tk.Text(frame_chat, height=8, width=93)
        self.text_chat.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        tk.Label(frame_chat, text="Your message:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.text_user_message = tk.Text(frame_chat, height=4, width=93)
        self.text_user_message.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        frame_chat_buttons = tk.Frame(frame_chat)
        frame_chat_buttons.grid(row=3, column=0, padx=5, pady=5, columnspan=3, sticky="w")

        self.button_send = tk.Button(
            frame_chat_buttons,
            text="Send message",
            command=self.generate,
            width=20,
            state="disabled",
        )
        self.button_send.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.button_regenerate = tk.Button(
            frame_chat_buttons,
            text="Regenerate last",
            command=self.regenerate,
            width=20,
            state="disabled",
        )
        self.button_regenerate.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.label_generation = tk.Label(frame_chat_buttons, text="Send message to start")
        self.label_generation.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.button_save = tk.Button(
            frame_chat_buttons,
            text="Save game",
            command=self.save_game,
            width=20,
            state="normal",
        )
        self.button_save.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.button_load = tk.Button(
            frame_chat_buttons,
            text="Load game",
            command=self.load_game,
            width=20,
            state="normal",
        )
        self.button_load.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.label_save_load = tk.Label(frame_chat_buttons, text="")
        self.label_save_load.grid(row=1, column=2, padx=5, pady=5, sticky="w")

    def _set_server_url_from_provider(self, provider_name: str) -> None:
        base_url = ""
        for provider in self.providers:
            if provider["name"] == provider_name:
                base_url = provider["base_url"]
                break

        self.entry_server_url.config(state="normal")
        self.entry_server_url.delete(0, tk.END)
        self.entry_server_url.insert(0, base_url)

    def on_provider_selected(self, event: tk.Event) -> None:
        self._set_server_url_from_provider(event.widget.get())

    def on_model_selected(self, event: tk.Event) -> None:
        model_id = event.widget.get()
        self._apply_model_selection(model_id)

    def _apply_model_selection(self, model_id: str) -> None:
        result = self.rpg_client.set_active_model(model_id)
        if result.ok:
            self.label_connection.config(text=f"Connected ({model_id})")
            return

        self.label_connection.config(text=f"Model error: {result.error}")
        self.disconnect()

    def _connect_worker(self, base_url: str, api_key: str) -> None:
        result = self.rpg_client.connect_to_llm(base_url=base_url, api_key=api_key)
        self.after(0, self._on_connect_finished, result)

    def _on_connect_finished(self, result: OperationResult) -> None:
        self.button_connect.config(state="normal")

        if not result.ok:
            self.disconnect()
            self.label_connection.config(text=f"Connection error: {result.error}")
            return

        model_ids = result.value or []
        self.model_ids = list(model_ids)
        self.entry_server_url.config(state="readonly")
        self.entry_api_key.config(state="readonly")
        self.button_disconnect.config(state="normal")
        self.label_connection.config(text="Connected")

        self.combobox_model.config(state="readonly", values=self.model_ids)
        if self.model_ids:
            self.combobox_model.set(self.model_ids[0])
            self._apply_model_selection(self.model_ids[0])

        self.button_send.config(state="normal")
        self.button_regenerate.config(state="normal")

    def connect(self) -> None:
        base_url = self.entry_server_url.get().strip()
        api_key = self.entry_api_key.get().strip()

        self.button_connect.config(state="disabled")
        self.button_disconnect.config(state="disabled")
        self.label_connection.config(text="Connecting...")

        threading.Thread(
            target=self._connect_worker,
            args=(base_url, api_key),
            daemon=True,
        ).start()

    def disconnect(self) -> None:
        self.rpg_client.disconnect_from_llm()
        self.model_ids = []
        self.label_connection.config(text="Disconnected")

        self.entry_server_url.config(state="normal")
        self.entry_api_key.config(state="normal")
        self.button_connect.config(state="normal")
        self.button_disconnect.config(state="normal")

        self.combobox_model.set("")
        self.combobox_model.config(state="disabled", values=[])
        self.button_send.config(state="disabled")
        self.button_regenerate.config(state="disabled")

    def _generate_worker(
        self,
        character_name: str,
        character_description: str,
        world_description: str,
        message_history: str,
    ) -> None:
        result = self.rpg_client.generate_response(
            character_name=character_name,
            character_description=character_description,
            world_description=world_description,
            message_history=message_history,
        )
        self.after(0, self._on_generation_finished, result)

    def _on_generation_finished(self, result: OperationResult) -> None:
        self.button_send.config(state="normal")
        self.button_regenerate.config(state="normal")
        self.text_chat.config(state="normal")

        if result.ok:
            self.label_generation.config(text="Generation done")
            self.text_chat.insert(tk.END, result.value)
            return

        self.label_generation.config(text=f"Generation error: {result.error}")
        logger.error("Generation failed: %s", result.error)

    def generate(self) -> None:
        user_text = self.text_user_message.get("1.0", "end-1c").strip()
        player_name = self.entry_player_name.get().strip() or "Player"
        user_message = f"{player_name}: {user_text}".strip()

        if not user_text:
            self.label_generation.config(text="Generation error: message is empty")
            return

        character_name = self.entry_character_name.get().strip()
        character_description = self.text_character_description.get("1.0", "end-1c").strip()
        world_description = self.text_world_description.get("1.0", "end-1c").strip()
        chat_history = self.text_chat.get("1.0", "end-1c").strip()

        if chat_history:
            message_history = f"{chat_history}\n{user_message}"
        else:
            message_history = user_message

        self.button_send.config(state="disabled")
        self.button_regenerate.config(state="disabled")
        self.label_generation.config(text="Generating...")

        self.text_user_message.delete("1.0", tk.END)
        self.text_chat.insert(tk.END, user_message)
        self.text_chat.config(state="disabled")

        threading.Thread(
            target=self._generate_worker,
            args=(
                character_name,
                character_description,
                world_description,
                message_history,
            ),
            daemon=True,
        ).start()

    def regenerate(self) -> None:
        self.label_generation.config(text="Not implemented yet")

    def save_game(self) -> None:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save as",
        )
        if not file_path:
            return

        data = {
            "server_url": self.entry_server_url.get(),
            "server_api": self.entry_api_key.get(),
            "char_name": self.entry_character_name.get(),
            "player_name": self.entry_player_name.get(),
            "char_desc": self.text_character_description.get("1.0", "end-1c"),
            "world_desc": self.text_world_description.get("1.0", "end-1c"),
            "chat": self.text_chat.get("1.0", "end-1c"),
        }

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            self.label_save_load.config(text="Game successfully saved")
        except OSError as exc:
            logger.exception("Failed to save game.")
            self.label_save_load.config(text=f"Save error: {exc}")

    def load_game(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load from",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            self.label_save_load.config(text="File not found")
            return
        except json.JSONDecodeError as exc:
            self.label_save_load.config(text=f"Wrong JSON format: {exc}")
            return
        except OSError as exc:
            logger.exception("Failed to load save file.")
            self.label_save_load.config(text=f"Load error: {exc}")
            return

        self.entry_server_url.config(state="normal")
        self.entry_server_url.delete(0, tk.END)
        self.entry_server_url.insert(0, data.get("server_url", ""))

        self.entry_api_key.config(state="normal")
        self.entry_api_key.delete(0, tk.END)
        self.entry_api_key.insert(0, data.get("server_api", ""))

        self.entry_character_name.delete(0, tk.END)
        self.entry_character_name.insert(0, data.get("char_name", ""))

        self.entry_player_name.delete(0, tk.END)
        self.entry_player_name.insert(0, data.get("player_name", ""))

        self.text_character_description.delete("1.0", tk.END)
        self.text_character_description.insert("1.0", data.get("char_desc", ""))

        self.text_world_description.delete("1.0", tk.END)
        self.text_world_description.insert("1.0", data.get("world_desc", ""))

        self.text_chat.config(state="normal")
        self.text_chat.delete("1.0", tk.END)
        self.text_chat.insert("1.0", data.get("chat", ""))

        self.label_save_load.config(text="Game successfully loaded")


# Backward compatibility for old imports.
RPG_ui = RPGUI
