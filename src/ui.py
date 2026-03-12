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
        self.stream = True

        self.providers = AppSettings.BASE_CONNECTION_OPTIONS
        self.provider_names = [provider["name"] for provider in self.providers]
        self.default_provider = self.providers[0]
        self.default_provider_name = self.default_provider["name"]
        self.model_ids: list[str] = []
        self._chat_is_programmatic_update = False
        self._chat_changed_since_last_generation = True
        self._last_response_start_index: str | None = None
        self._stream_has_chunks = False
        self.default_token_limit = 4096
        self.min_token_limit = 1
        self.max_token_limit = 200000
        self.token_limit_var = tk.IntVar(value=self.default_token_limit)

        self._build_layout()
        self._set_server_url_from_provider(self.default_provider_name)

    def _build_layout(self) -> None:
        self.title("RPG Chat Client")
        self.geometry("900x650")
        self.minsize(720, 520)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._layout_max_width = 980

        self.main_canvas = tk.Canvas(self, highlightthickness=0)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")

        self.main_scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.main_canvas.yview
        )
        self.main_scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        frame_global = tk.Frame(self.main_canvas, padx=10, pady=20)
        self._global_window = self.main_canvas.create_window(
            (0, 0), window=frame_global, anchor="n"
        )
        self.main_canvas.bind("<Configure>", self._on_canvas_configure)
        frame_global.bind("<Configure>", self._on_content_configure)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        frame_global.grid_columnconfigure(0, weight=1)
        frame_global.grid_rowconfigure(2, weight=1)

        frame_server = tk.LabelFrame(frame_global, text="Server Information")
        frame_server.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        frame_server.grid_columnconfigure(1, weight=1)
        frame_server.grid_columnconfigure(2, weight=1)

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
        self.combobox_provider.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(frame_server, text="Presets").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )

        tk.Label(frame_server, text="Server URL:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_server_url = tk.Entry(frame_server, width=40)
        self.entry_server_url.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        tk.Label(
            frame_server,
            text="Example: https://api.openai.com/v1/ (OpenAI-compatible only)",
        ).grid(row=1, column=2, padx=5, pady=5, sticky="w")

        tk.Label(frame_server, text="API key:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_api_key = tk.Entry(frame_server, width=40, show="*")
        self.entry_api_key.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        tk.Label(frame_server, text="Leave blank for local models").grid(
            row=2, column=2, padx=5, pady=5, sticky="w"
        )

        frame_server_buttons = tk.Frame(frame_server)
        frame_server_buttons.grid(row=3, column=0, padx=5, pady=5, columnspan=3, sticky="ew")
        frame_server_buttons.grid_columnconfigure(2, weight=1)

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
        frame_world_character.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        frame_world_character.grid_columnconfigure(0, weight=1)
        frame_world_character.grid_columnconfigure(1, weight=2)
        frame_world_character.grid_columnconfigure(2, weight=2)
        frame_world_character.grid_rowconfigure(1, weight=1)

        tk.Label(frame_world_character, text="Model:").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )
        self.combobox_model = ttk.Combobox(
            frame_world_character, values=self.model_ids, state="disabled"
        )
        self.combobox_model.bind("<<ComboboxSelected>>", self.on_model_selected)
        self.combobox_model.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        tk.Label(frame_world_character, text="Token limit:").grid(
            row=2, column=0, padx=5, pady=5, sticky="w"
        )
        token_limit_validator = (self.register(self._validate_token_limit_input), "%P")
        self.spinbox_token_limit = tk.Spinbox(
            frame_world_character,
            from_=self.min_token_limit,
            to=self.max_token_limit,
            textvariable=self.token_limit_var,
            width=10,
            increment=512,
            validate="key",
            validatecommand=token_limit_validator,
        )
        self.spinbox_token_limit.bind("<FocusOut>", self._on_token_limit_focus_out)
        self.spinbox_token_limit.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        tk.Label(frame_world_character, text="Character name:").grid(
            row=4, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_character_name = tk.Entry(frame_world_character)
        self.entry_character_name.grid(row=5, column=0, padx=5, pady=5, sticky="ew")

        tk.Label(frame_world_character, text="Player name:").grid(
            row=6, column=0, padx=5, pady=5, sticky="w"
        )
        self.entry_player_name = tk.Entry(frame_world_character)
        self.entry_player_name.grid(row=7, column=0, padx=5, pady=5, sticky="ew")

        tk.Label(frame_world_character, text="World Information and Scenario").grid(
            row=0, column=1, padx=5, pady=5, sticky="w"
        )
        self.text_world_description = tk.Text(
            frame_world_character, height=10, width=31, wrap="word"
        )
        self.text_world_description.grid(
            row=1, column=1, padx=5, pady=5, sticky="nsew", rowspan=8
        )

        tk.Label(frame_world_character, text="Character Information").grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.text_character_description = tk.Text(
            frame_world_character, height=10, width=31, wrap="word"
        )
        self.text_character_description.grid(
            row=1, column=2, padx=5, pady=5, sticky="nsew", rowspan=8
        )

        frame_chat = tk.LabelFrame(frame_global, text="Chat")
        frame_chat.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        frame_chat.grid_columnconfigure(0, weight=1)
        frame_chat.grid_rowconfigure(0, weight=1)
        frame_chat.grid_rowconfigure(2, weight=1)

        self.text_chat = tk.Text(frame_chat, height=16, width=93, wrap="word")
        self.text_chat.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.text_chat.bind("<<Modified>>", self._on_chat_modified)

        tk.Label(frame_chat, text="Your message:").grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )
        self.text_user_message = tk.Text(frame_chat, height=4, width=93, wrap="word")
        self.text_user_message.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        frame_chat_buttons = tk.Frame(frame_chat)
        frame_chat_buttons.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        frame_chat_buttons.grid_columnconfigure(2, weight=1)

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

    def _on_canvas_configure(self, event: tk.Event) -> None:
        content_width = min(event.width, self._layout_max_width)
        x_offset = max((event.width - content_width) // 2, 0)
        self.main_canvas.coords(self._global_window, x_offset, 0)
        self.main_canvas.itemconfigure(self._global_window, width=content_width)

    def _on_content_configure(self, event: tk.Event) -> None:
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.main_canvas.winfo_exists():
            self.main_canvas.yview_scroll(int(-event.delta / 120), "units")

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
        token_limit: int,
        stream_mode: bool,
    ) -> None:
        if stream_mode:
            result = self.rpg_client.generate_response_stream(
                character_name=character_name,
                character_description=character_description,
                world_description=world_description,
                message_history=message_history,
                token_limit=token_limit,
                on_chunk=lambda chunk: self.after(0, self._on_stream_chunk, chunk),
            )
            self.after(0, self._on_stream_finished, result)
            return

        result = self.rpg_client.generate_response(
            character_name=character_name,
            character_description=character_description,
            world_description=world_description,
            message_history=message_history,
            token_limit=token_limit,
        )
        self.after(0, self._on_generation_finished, result)

    def _validate_token_limit_input(self, proposed_value: str) -> bool:
        if not proposed_value:
            return False
        if not proposed_value.isdigit():
            return False

        parsed_value = int(proposed_value)
        return self.min_token_limit <= parsed_value <= self.max_token_limit

    def _on_token_limit_focus_out(self, event: tk.Event) -> None:
        self._get_token_limit()

    def _get_token_limit(self) -> int:
        raw_value = self.spinbox_token_limit.get().strip()
        try:
            token_limit = int(raw_value)
        except ValueError:
            token_limit = self.default_token_limit

        if token_limit < self.min_token_limit:
            token_limit = self.default_token_limit
        elif token_limit > self.max_token_limit:
            token_limit = self.max_token_limit

        self.token_limit_var.set(token_limit)
        return token_limit

    def _on_chat_modified(self, event: tk.Event) -> None:
        if not self.text_chat.edit_modified():
            return

        if not self._chat_is_programmatic_update:
            self._chat_changed_since_last_generation = True
            self.button_regenerate.config(state="disabled")

        self.text_chat.edit_modified(False)

    def _insert_chat_text(self, text: str) -> None:
        self._chat_is_programmatic_update = True
        try:
            self.text_chat.insert(tk.END, text)
            self._scroll_chat_to_bottom()
        finally:
            self._chat_is_programmatic_update = False
            self.text_chat.edit_modified(False)

    def _scroll_chat_to_bottom(self) -> None:
        self.text_chat.see(tk.END)
        self.text_chat.yview_moveto(1.0)

    def _append_chat_message(self, speaker: str, content: str) -> None:
        message = f"{speaker}: {content}".strip()
        existing = self.text_chat.get("1.0", "end-1c")
        normalized_existing = existing.rstrip("\n")

        if normalized_existing:
            self._delete_chat_text("1.0", tk.END)
            self._insert_chat_text(normalized_existing + "\n\n" + message + "\n\n")
        else:
            self._insert_chat_text(message + "\n\n")

    def _delete_chat_text(self, start: str, end: str) -> None:
        self._chat_is_programmatic_update = True
        try:
            self.text_chat.delete(start, end)
        finally:
            self._chat_is_programmatic_update = False
            self.text_chat.edit_modified(False)

    def _on_generation_finished(self, result: OperationResult) -> None:
        self.button_send.config(state="normal")
        self.button_regenerate.config(state="disabled")
        self.text_chat.config(state="normal")

        char_name = self.entry_character_name.get()

        if result.ok:
            self._last_response_start_index = self.text_chat.index("end-1c")
            self.label_generation.config(text="Generation done")
            self._append_chat_message(char_name, result.value)
            self._chat_changed_since_last_generation = False
            self.button_regenerate.config(state="normal")
            return

        self._last_response_start_index = None
        self._chat_changed_since_last_generation = True
        self.label_generation.config(text=f"Generation error: {result.error}")
        logger.error("Generation failed: %s", result.error)

    def _start_stream_message(self, speaker: str) -> None:
        self._stream_has_chunks = False
        self._last_response_start_index = self.text_chat.index("end-1c")
        existing = self.text_chat.get("1.0", "end-1c")
        normalized_existing = existing.rstrip("\n")
        message_start = f"{speaker}: "

        self.text_chat.config(state="normal")
        if normalized_existing:
            self._delete_chat_text("1.0", tk.END)
            self._insert_chat_text(normalized_existing + "\n\n" + message_start)
        else:
            self._insert_chat_text(message_start)
        self.text_chat.config(state="disabled")

    def _on_stream_chunk(self, chunk: str) -> None:
        if not chunk:
            return
        self._stream_has_chunks = True
        self.text_chat.config(state="normal")
        self._insert_chat_text(chunk)
        self.text_chat.config(state="disabled")

    def _on_stream_finished(self, result: OperationResult) -> None:
        self.button_send.config(state="normal")
        self.button_regenerate.config(state="disabled")
        self.text_chat.config(state="normal")

        if result.ok and self._stream_has_chunks:
            self._insert_chat_text("\n\n")
            self.label_generation.config(text="Generation done")
            self._chat_changed_since_last_generation = False
            self.button_regenerate.config(state="normal")
            return

        if self._last_response_start_index is not None:
            self._delete_chat_text(self._last_response_start_index, tk.END)

        self._last_response_start_index = None
        self._chat_changed_since_last_generation = True
        if result.ok:
            self.label_generation.config(text="Generation error: empty response")
            logger.error("Generation failed: empty streaming response.")
        else:
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
            message_history = f"{chat_history}\n\n{user_message}"
        else:
            message_history = user_message
        token_limit = self._get_token_limit()

        self.button_send.config(state="disabled")
        self.button_regenerate.config(state="disabled")
        self.label_generation.config(text="Generating...")

        self.text_user_message.delete("1.0", tk.END)
        self._append_chat_message(player_name, user_text)
        if self.stream:
            self._start_stream_message(character_name)
        else:
            self.text_chat.config(state="disabled")

        threading.Thread(
            target=self._generate_worker,
            args=(
                character_name,
                character_description,
                world_description,
                message_history,
                token_limit,
                self.stream,
            ),
            daemon=True,
        ).start()

    def regenerate(self) -> None:
        if self._chat_changed_since_last_generation or not self._last_response_start_index:
            self.label_generation.config(text="Regenerate unavailable: chat was changed")
            self.button_regenerate.config(state="disabled")
            return

        self.text_chat.config(state="normal")
        self._delete_chat_text(self._last_response_start_index, tk.END)
        self.text_chat.config(state="disabled")

        character_name = self.entry_character_name.get().strip()
        character_description = self.text_character_description.get("1.0", "end-1c").strip()
        world_description = self.text_world_description.get("1.0", "end-1c").strip()
        message_history = self.text_chat.get("1.0", "end-1c").strip()
        token_limit = self._get_token_limit()

        if not message_history:
            self.label_generation.config(text="Regenerate error: message history is empty")
            self._last_response_start_index = None
            self._chat_changed_since_last_generation = True
            self.button_regenerate.config(state="disabled")
            return

        self.button_send.config(state="disabled")
        self.button_regenerate.config(state="disabled")
        self.label_generation.config(text="Regenerating...")
        if self.stream:
            self._start_stream_message(character_name)

        threading.Thread(
            target=self._generate_worker,
            args=(
                character_name,
                character_description,
                world_description,
                message_history,
                token_limit,
                self.stream,
            ),
            daemon=True,
        ).start()

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
            "token_limit": self._get_token_limit(),
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
        self._insert_chat_text(data.get("chat", ""))
        saved_token_limit = data.get("token_limit", self.default_token_limit)
        try:
            token_limit = int(saved_token_limit)
        except (TypeError, ValueError):
            token_limit = self.default_token_limit
        if token_limit < self.min_token_limit:
            token_limit = self.default_token_limit
        elif token_limit > self.max_token_limit:
            token_limit = self.max_token_limit
        self.token_limit_var.set(token_limit)
        self._last_response_start_index = None
        self._chat_changed_since_last_generation = True
        self.button_regenerate.config(state="disabled")

        self.label_save_load.config(text="Game successfully loaded")
