from __future__ import annotations

import json
import logging
import threading
from queue import Empty, Queue
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from chat_controller import ChatController
from models import DEFAULT_SETTINGS, GameState

logger = logging.getLogger(__name__)


class RPGChatUI:
    def __init__(self, root: Tk, controller: ChatController, state: GameState) -> None:
        self.root = root
        self.controller = controller
        self.state = state

        self._stream_queue: Queue[tuple[str, str]] = Queue()
        self._streaming = False
        self._summary_running = False
        self._stream_speaker = ""
        self._stream_buffer = ""
        self._last_request_tokens = 0
        self._last_prompt_debug_signature: tuple[int, int, int] | None = None

        self.player_name_var = StringVar(value=self.state.player_name)
        self.character_name_var = StringVar(value=self.state.character_name)
        self.server_status_var = StringVar(value="LM Studio: Unknown")
        initial_base_url = self.controller.set_llm_base_url(
            str(self.state.settings.get("llm_base_url", self.controller.get_default_llm_base_url()))
        )
        self.state.settings["llm_base_url"] = initial_base_url
        self.llm_base_url_var = StringVar(value=initial_base_url)
        self.llm_status_var = StringVar(value="LLM: Idle")
        initial_context_limit = self._safe_int(
            str(self.state.settings.get("context_limit", self.controller.get_memory_limit())),
            self.controller.get_memory_limit(),
        )
        self.controller.set_memory_limit(initial_context_limit)
        self.memory_limit_var = StringVar(value=str(initial_context_limit))

        self.temperature_var = StringVar(
            value=str(self.state.settings.get("temperature", DEFAULT_SETTINGS["temperature"]))
        )
        self.top_p_var = StringVar(value=str(self.state.settings.get("top_p", DEFAULT_SETTINGS["top_p"])))
        self.presence_penalty_var = StringVar(
            value=str(
                self.state.settings.get("presence_penalty", DEFAULT_SETTINGS["presence_penalty"])
            )
        )
        self.frequency_penalty_var = StringVar(
            value=str(
                self.state.settings.get("frequency_penalty", DEFAULT_SETTINGS["frequency_penalty"])
            )
        )
        self.max_tokens_var = StringVar(
            value=str(self.state.settings.get("max_tokens", DEFAULT_SETTINGS["max_tokens"]))
        )
        self.prompt_debug_var = BooleanVar(
            value=bool(self.state.settings.get("prompt_debug", DEFAULT_SETTINGS["prompt_debug"]))
        )

        self.context_tokens_var = StringVar(value="Context tokens: 0 / 0")
        self.last_request_var = StringVar(value="Last request: 0 tokens")

        self.advanced_visible = False

        self._configure_root()
        self._build_layout()
        self._bind_events()
        self._refresh_server_status()
        self.refresh_chat_history()
        self.update_token_monitor()

    def _configure_root(self) -> None:
        self.root.title("RPG Chat Client v2.01")
        self.root.geometry("960x900")
        self.root.minsize(820, 700)

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content_frame = ttk.Frame(self.canvas)

        self.content_frame.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._build_server_status_section()
        self._build_character_setup_section()
        self._build_descriptions_section()
        self._build_story_intent_section()
        self._build_scene_memory_section()
        self._build_chat_history_section()
        self._build_message_input_section()
        self._build_controls_section()
        self._build_token_monitor_section()
        self._build_advanced_options_section()

    def _build_server_status_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Server Status")
        frame.pack(fill=tk.X, padx=10, pady=6)

        ttk.Label(frame, textvariable=self.server_status_var).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Button(frame, text="Reconnect", command=self._on_reconnect).grid(
            row=0, column=1, padx=6, pady=6
        )

        ttk.Label(frame, text="LM Studio URL:").grid(row=0, column=2, sticky="e", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.llm_base_url_var, width=26).grid(
            row=0, column=3, sticky="w", padx=6, pady=6
        )
        ttk.Button(frame, text="Reset Default URL", command=self._on_reset_default_url).grid(
            row=0, column=4, padx=6, pady=6
        )

        ttk.Label(frame, text="Memory Limit:").grid(row=1, column=2, sticky="e", padx=6, pady=(0, 6))
        ttk.Entry(frame, textvariable=self.memory_limit_var, width=10).grid(
            row=1, column=3, sticky="w", padx=6, pady=(0, 6)
        )

        frame.columnconfigure(0, weight=1)

    def _build_character_setup_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Character Setup")
        frame.pack(fill=tk.X, padx=10, pady=6)

        ttk.Label(frame, text="Player Name").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.player_name_var, width=24).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(frame, text="Character Name").grid(row=0, column=2, sticky="w", padx=6, pady=6)
        ttk.Entry(frame, textvariable=self.character_name_var, width=24).grid(
            row=0, column=3, sticky="w", padx=6, pady=6
        )

    def _build_descriptions_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Descriptions")
        frame.pack(fill=tk.BOTH, padx=10, pady=6)

        ttk.Label(frame, text="Player Description").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 2))
        self.player_description_text = ScrolledText(
            frame, height=5, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1
        )
        self.player_description_text.grid(row=1, column=0, sticky="nsew", padx=6, pady=2)
        ttk.Label(frame, text="Write short lines. One line = one idea.").grid(
            row=2, column=0, sticky="w", padx=6, pady=(0, 6)
        )

        ttk.Label(frame, text="Character Description").grid(row=3, column=0, sticky="w", padx=6, pady=(6, 2))
        self.character_description_text = ScrolledText(
            frame, height=5, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1
        )
        self.character_description_text.grid(row=4, column=0, sticky="nsew", padx=6, pady=2)
        ttk.Label(frame, text="Write short lines. One line = one idea.").grid(
            row=5, column=0, sticky="w", padx=6, pady=(0, 6)
        )

        ttk.Label(frame, text="World Description").grid(row=6, column=0, sticky="w", padx=6, pady=(6, 2))
        self.world_scenario_text = ScrolledText(
            frame, height=6, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1
        )
        self.world_scenario_text.grid(row=7, column=0, sticky="nsew", padx=6, pady=2)
        ttk.Label(frame, text="Describe world rules, factions, places, and atmosphere.").grid(
            row=8, column=0, sticky="w", padx=6, pady=(0, 6)
        )

        frame.columnconfigure(0, weight=1)

    def _build_story_intent_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Story Intent")
        frame.pack(fill=tk.BOTH, padx=10, pady=6)

        self.story_intent_text = ScrolledText(
            frame, height=5, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1
        )
        self.story_intent_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 2))
        ttk.Label(
            frame,
            text="Guide the trajectory and tone of the story in short lines.",
        ).pack(anchor="w", padx=6, pady=(0, 6))

    def _build_scene_memory_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Scene Memory")
        frame.pack(fill=tk.BOTH, padx=10, pady=6)

        self.scene_memory_text = ScrolledText(
            frame, height=6, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1
        )
        self.scene_memory_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 2))
        ttk.Label(
            frame,
            text="Keep summarized past events here as short factual lines.",
        ).pack(anchor="w", padx=6, pady=(0, 6))

    def _build_chat_history_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Chat History")
        frame.pack(fill=tk.BOTH, padx=10, pady=6)

        self.chat_history_text = ScrolledText(frame, height=14, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_history_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 2))
        ttk.Label(
            frame,
            text="Read-only conversation view. Use 'Delete Last Message' to remove the latest turn.",
        ).pack(anchor="w", padx=6, pady=(0, 6))

    def _build_message_input_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Message Input")
        frame.pack(fill=tk.BOTH, padx=10, pady=6)

        self.message_input_text = ScrolledText(
            frame, height=4, wrap=tk.WORD, undo=True, autoseparators=True, maxundo=-1
        )
        self.message_input_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _build_controls_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Controls")
        frame.pack(fill=tk.X, padx=10, pady=6)

        status_row = ttk.Frame(frame)
        status_row.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        ttk.Label(status_row, textvariable=self.llm_status_var).pack(side=tk.LEFT, padx=(0, 8))
        self.llm_progress = ttk.Progressbar(status_row, mode="indeterminate", length=120)
        self.llm_progress.pack(side=tk.LEFT)

        chat_frame = ttk.LabelFrame(frame, text="Chat")
        chat_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=6)
        persistence_frame = ttk.LabelFrame(frame, text="Persistence")
        persistence_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))

        primary_chat_frame = ttk.LabelFrame(chat_frame, text="Primary")
        primary_chat_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        utility_chat_frame = ttk.LabelFrame(chat_frame, text="Utilities")
        utility_chat_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))

        self.send_button = ttk.Button(primary_chat_frame, text="Send Message", command=self._on_send_message)
        self.redo_button = ttk.Button(primary_chat_frame, text="Redo Response", command=self._on_redo_response)
        self.stop_button = ttk.Button(utility_chat_frame, text="Stop Generation", command=self._on_stop_generation)
        self.delete_last_button = ttk.Button(
            utility_chat_frame,
            text="Delete Last Message",
            command=self._on_delete_last_message,
        )
        self.summary_button = ttk.Button(utility_chat_frame, text="Make Summary", command=self._on_make_summary)
        self.save_button = ttk.Button(persistence_frame, text="Save Game", command=self._on_save_game)
        self.load_button = ttk.Button(persistence_frame, text="Load Game", command=self._on_load_game)

        primary_chat_buttons = [
            self.send_button,
            self.redo_button,
        ]
        utility_chat_buttons = [
            self.stop_button,
            self.delete_last_button,
            self.summary_button,
        ]
        persistence_buttons = [
            self.save_button,
            self.load_button,
        ]

        for idx, button in enumerate(primary_chat_buttons):
            button.grid(row=0, column=idx, padx=6, pady=6, sticky="ew")

        for idx, button in enumerate(utility_chat_buttons):
            button.grid(row=0, column=idx, padx=6, pady=6, sticky="ew")

        for idx, button in enumerate(persistence_buttons):
            button.grid(row=0, column=idx, padx=6, pady=6, sticky="ew")

        for col in range(2):
            primary_chat_frame.columnconfigure(col, weight=1)
        for col in range(3):
            utility_chat_frame.columnconfigure(col, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        for col in range(2):
            persistence_frame.columnconfigure(col, weight=1)

        frame.columnconfigure(0, weight=1)

    def _build_token_monitor_section(self) -> None:
        frame = ttk.LabelFrame(self.content_frame, text="Token Monitor")
        frame.pack(fill=tk.X, padx=10, pady=6)

        self.context_tokens_label = ttk.Label(frame, textvariable=self.context_tokens_var)
        self.context_tokens_label.pack(anchor="w", padx=6, pady=(6, 2))

        self.last_request_label = ttk.Label(frame, textvariable=self.last_request_var)
        self.last_request_label.pack(anchor="w", padx=6, pady=(2, 6))

    def _build_advanced_options_section(self) -> None:
        section = ttk.LabelFrame(self.content_frame, text="Advanced Options")
        section.pack(fill=tk.X, padx=10, pady=6)

        self.advanced_toggle_button = ttk.Button(
            section,
            text="Show Advanced Options",
            command=self._toggle_advanced_options,
        )
        self.advanced_toggle_button.pack(anchor="w", padx=6, pady=6)

        self.advanced_frame = ttk.Frame(section)

        ttk.Label(
            self.advanced_frame,
            text="Lower values are more stable. Higher values are more creative but less consistent.",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=6, pady=(4, 2))

        self._labeled_entry(
            self.advanced_frame,
            "Temperature",
            self.temperature_var,
            1,
            "Allowed 0.5-0.9, default 0.7.",
        )
        self._labeled_entry(
            self.advanced_frame,
            "Top P",
            self.top_p_var,
            2,
            "Allowed 0.8-0.95, default 0.9.",
        )
        self._labeled_entry(
            self.advanced_frame,
            "Presence Penalty",
            self.presence_penalty_var,
            3,
            "Allowed 0.0-0.6, default 0.3.",
        )
        self._labeled_entry(
            self.advanced_frame,
            "Frequency Penalty",
            self.frequency_penalty_var,
            4,
            "Allowed 0.0-0.5, default 0.2.",
        )
        self._labeled_entry(
            self.advanced_frame,
            "Max Tokens",
            self.max_tokens_var,
            5,
            "Default 120. Keeps replies around moderate length.",
        )

        ttk.Button(
            self.advanced_frame,
            text="Reset Recommended",
            command=self._reset_advanced_defaults,
        ).grid(row=6, column=0, sticky="w", padx=6, pady=6)

        ttk.Checkbutton(
            self.advanced_frame,
            text="Prompt Debug Mode",
            variable=self.prompt_debug_var,
        ).grid(row=7, column=0, columnspan=2, sticky="w", padx=6, pady=(4, 2))
        ttk.Label(
            self.advanced_frame,
            text="When enabled: logs context token usage and prompt metadata to app console.",
        ).grid(row=8, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 6))
        ttk.Label(
            self.advanced_frame,
            text="Values above ranges are auto-limited to avoid unstable roleplay.",
        ).grid(row=9, column=0, columnspan=3, sticky="w", padx=6, pady=(0, 6))

        self._load_state_into_fields()

    def _labeled_entry(
        self,
        parent: ttk.Frame,
        label: str,
        variable: StringVar,
        row: int,
        hint: str,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(parent, textvariable=variable, width=18).grid(
            row=row,
            column=1,
            sticky="w",
            padx=6,
            pady=4,
        )
        ttk.Label(parent, text=hint).grid(row=row, column=2, sticky="w", padx=6, pady=4)

    def _reset_advanced_defaults(self) -> None:
        self.temperature_var.set(str(DEFAULT_SETTINGS["temperature"]))
        self.top_p_var.set(str(DEFAULT_SETTINGS["top_p"]))
        self.presence_penalty_var.set(str(DEFAULT_SETTINGS["presence_penalty"]))
        self.frequency_penalty_var.set(str(DEFAULT_SETTINGS["frequency_penalty"]))
        self.max_tokens_var.set(str(DEFAULT_SETTINGS["max_tokens"]))
        self.prompt_debug_var.set(bool(DEFAULT_SETTINGS["prompt_debug"]))
        self.update_token_monitor()

    def _bind_events(self) -> None:
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.message_input_text.bind("<KeyRelease>", self._on_input_changed, add="+")
        self._bind_clipboard_shortcuts()

    def _bind_clipboard_shortcuts(self) -> None:
        # Keep default Tk bindings for Ctrl+C/X/V to avoid platform/layout regressions.
        # Add only alternative clipboard shortcuts explicitly.
        clipboard_events = {
            "<Control-Insert>": "<<Copy>>",
            "<Shift-Insert>": "<<Paste>>",
            "<Shift-Delete>": "<<Cut>>",
        }

        for class_name in ("Text", "Entry", "TEntry"):
            for sequence, virtual_event in clipboard_events.items():
                self.root.bind_class(
                    class_name,
                    sequence,
                    lambda event, ve=virtual_event: self._forward_virtual_event(event, ve),
                    add="+",
                )
            self.root.bind_class(
                class_name,
                "<Control-KeyPress>",
                self._on_control_keypress,
                add="+",
            )

            self.root.bind_class(
                class_name,
                "<Control-a>",
                self._on_select_all,
                add="+",
            )
            self.root.bind_class(
                class_name,
                "<Control-A>",
                self._on_select_all,
                add="+",
            )

    def _forward_virtual_event(self, event: tk.Event, virtual_event: str) -> str:
        event.widget.event_generate(virtual_event)
        return "break"

    def _on_control_keypress(self, event: tk.Event) -> str | None:
        keycode = int(getattr(event, "keycode", -1))
        keysym = str(getattr(event, "keysym", "")).lower()

        copy_keysyms = {"c", "cyrillic_es"}
        cut_keysyms = {"x", "cyrillic_che"}
        paste_keysyms = {"v", "cyrillic_em"}
        select_all_keysyms = {"a", "cyrillic_ef"}
        undo_keysyms = {"z", "cyrillic_ya"}
        redo_keysyms = {"y", "cyrillic_en"}

        if keycode == 67 or keysym in copy_keysyms:
            event.widget.event_generate("<<Copy>>")
            return "break"
        if keycode == 88 or keysym in cut_keysyms:
            event.widget.event_generate("<<Cut>>")
            return "break"
        if keycode == 86 or keysym in paste_keysyms:
            event.widget.event_generate("<<Paste>>")
            return "break"
        if keycode == 65 or keysym in select_all_keysyms:
            return self._on_select_all(event)
        if keycode == 90 or keysym in undo_keysyms:
            event.widget.event_generate("<<Undo>>")
            return "break"
        if keycode == 89 or keysym in redo_keysyms:
            event.widget.event_generate("<<Redo>>")
            return "break"

        return None

    def _on_select_all(self, event: tk.Event) -> str:
        widget = event.widget

        if isinstance(widget, tk.Text):
            widget.tag_add(tk.SEL, "1.0", "end-1c")
            widget.mark_set(tk.INSERT, "end-1c")
            widget.see(tk.INSERT)
            return "break"

        if isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.selection_range(0, tk.END)
            widget.icursor(tk.END)
            return "break"

        return "break"

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_input_changed(self, _event: tk.Event) -> None:
        self.root.after(0, self.update_token_monitor)

    def _toggle_advanced_options(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_frame.pack(fill=tk.X, padx=6, pady=(0, 6))
            self.advanced_toggle_button.configure(text="Hide Advanced Options")
        else:
            self.advanced_frame.pack_forget()
            self.advanced_toggle_button.configure(text="Show Advanced Options")

    def _load_state_into_fields(self) -> None:
        self.player_description_text.insert("1.0", self.state.player_description)
        self.character_description_text.insert("1.0", self.state.character_description)
        self.world_scenario_text.insert("1.0", self.state.world_scenario)
        self.story_intent_text.insert("1.0", self.state.story_intent)
        self.scene_memory_text.insert("1.0", self.state.scene_memory)

    def _read_text(self, widget: ScrolledText) -> str:
        return widget.get("1.0", tk.END).strip()

    def _push_fields_to_state(self) -> None:
        self.state.player_name = self.player_name_var.get().strip() or "Player"
        self.state.character_name = self.character_name_var.get().strip() or "Character"

        self.state.player_description = self._read_text(self.player_description_text)
        self.state.character_description = self._read_text(self.character_description_text)
        self.state.world_scenario = self._read_text(self.world_scenario_text)
        self.state.story_intent = self._read_text(self.story_intent_text)
        self.state.scene_memory = self._read_text(self.scene_memory_text)

        temperature = self._safe_clamped_float(
            self.temperature_var.get(),
            float(DEFAULT_SETTINGS["temperature"]),
            min_value=0.5,
            max_value=0.9,
        )
        top_p = self._safe_clamped_float(
            self.top_p_var.get(),
            float(DEFAULT_SETTINGS["top_p"]),
            min_value=0.8,
            max_value=0.95,
        )
        presence_penalty = self._safe_clamped_float(
            self.presence_penalty_var.get(),
            float(DEFAULT_SETTINGS["presence_penalty"]),
            min_value=0.0,
            max_value=0.6,
        )
        frequency_penalty = self._safe_clamped_float(
            self.frequency_penalty_var.get(),
            float(DEFAULT_SETTINGS["frequency_penalty"]),
            min_value=0.0,
            max_value=0.5,
        )
        self.temperature_var.set(f"{temperature:g}")
        self.top_p_var.set(f"{top_p:g}")
        self.presence_penalty_var.set(f"{presence_penalty:g}")
        self.frequency_penalty_var.set(f"{frequency_penalty:g}")

        self.controller.apply_generation_settings(
            temperature=temperature,
            top_p=top_p,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            max_tokens=self._safe_int(self.max_tokens_var.get(), int(DEFAULT_SETTINGS["max_tokens"])),
            prompt_debug=bool(self.prompt_debug_var.get()),
        )

        normalized_base_url = self.controller.set_llm_base_url(self.llm_base_url_var.get())
        self.llm_base_url_var.set(normalized_base_url)
        self.state.settings["llm_base_url"] = normalized_base_url

        new_limit = self._safe_int(
            self.memory_limit_var.get(),
            self.controller.get_memory_limit(),
        )
        self.controller.set_memory_limit(new_limit)
        self.state.settings["context_limit"] = new_limit

    def _safe_float(self, value: str, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_clamped_float(
        self,
        value: str,
        default: float,
        min_value: float,
        max_value: float,
    ) -> float:
        parsed = self._safe_float(value, default)
        if parsed < min_value:
            return min_value
        if parsed > max_value:
            return max_value
        return parsed

    def _safe_int(self, value: str, default: int) -> int:
        try:
            parsed = int(float(value))
        except (TypeError, ValueError):
            return default
        return max(1, parsed)

    def _on_reconnect(self) -> None:
        self._push_fields_to_state()
        self._refresh_server_status()

    def _on_reset_default_url(self) -> None:
        default_url = self.controller.get_default_llm_base_url()
        self.llm_base_url_var.set(default_url)
        self._push_fields_to_state()
        self._refresh_server_status()

    def _refresh_server_status(self) -> None:
        try:
            if self.controller.is_server_connected():
                self.server_status_var.set("LM Studio: Connected")
            else:
                self.server_status_var.set("LM Studio: Disconnected")
        except Exception:
            self.server_status_var.set("LM Studio: Disconnected")

    def _on_send_message(self) -> None:
        if self._streaming or self._summary_running:
            return

        self._push_fields_to_state()
        message = self._read_text(self.message_input_text)
        if not message:
            return

        turn = self.controller.send_player_message(message)
        if not turn:
            return

        self.message_input_text.delete("1.0", tk.END)
        self.refresh_chat_history()

        self._streaming = True
        self._stream_speaker = self.state.character_name.strip() or "Character"
        self._stream_buffer = ""
        self._set_generation_controls_enabled(False)
        self._set_llm_busy("Generating response...")

        thread = threading.Thread(target=self._stream_generation_worker, daemon=True)
        thread.start()
        self.root.after(50, self._poll_stream_queue)

    def _stream_generation_worker(self) -> None:
        try:
            response_text = self.controller.generate_character_response(
                stream=True,
                on_stream_token=lambda chunk: self._stream_queue.put(("chunk", chunk)),
            )
            self._stream_queue.put(("done", response_text))
        except Exception as exc:
            self._stream_queue.put(("error", str(exc)))

    def _poll_stream_queue(self) -> None:
        had_event = False
        while True:
            try:
                kind, payload = self._stream_queue.get_nowait()
            except Empty:
                break

            had_event = True
            if kind == "chunk":
                self._stream_buffer += payload
                normalized_stream_text = self.controller.normalize_character_text(self._stream_buffer)
                self.refresh_chat_history(transient_turn=(self._stream_speaker, normalized_stream_text))
            elif kind == "done":
                self._last_request_tokens = self.controller.estimate_text_tokens(payload)
                self._streaming = False
                self._stream_speaker = ""
                self._stream_buffer = ""
                self._set_generation_controls_enabled(True)
                self._set_llm_idle()
                self.refresh_chat_history()
                self.update_token_monitor()
            elif kind == "error":
                self._streaming = False
                self._stream_speaker = ""
                self._stream_buffer = ""
                self._set_generation_controls_enabled(True)
                self._set_llm_idle()
                messagebox.showerror("Generation Error", payload)
                self.refresh_chat_history()
                self.update_token_monitor()
            elif kind == "summary_done":
                summary = payload
                self._summary_running = False
                self._set_generation_controls_enabled(True)
                self._set_llm_idle()
                if summary:
                    self.scene_memory_text.delete("1.0", tk.END)
                    self.scene_memory_text.insert("1.0", self.state.scene_memory)
                    self._last_request_tokens = self.controller.estimate_text_tokens(summary)
                self.refresh_chat_history()
                self.update_token_monitor()
            elif kind == "summary_error":
                self._summary_running = False
                self._set_generation_controls_enabled(True)
                self._set_llm_idle()
                messagebox.showerror("Summary Error", payload)
                self.refresh_chat_history()
                self.update_token_monitor()

        if self._streaming or self._summary_running or had_event:
            self.root.after(50, self._poll_stream_queue)

    def _on_redo_response(self) -> None:
        if self._streaming or self._summary_running:
            return

        self._push_fields_to_state()
        if not self.state.chat_history:
            return
        last_turn = self.state.chat_history[-1]
        if not isinstance(last_turn, dict):
            messagebox.showwarning("Redo Response", "Last turn must be a Character response.")
            return
        if str(last_turn.get("speaker", "")).strip().lower() != "character":
            messagebox.showwarning("Redo Response", "Last turn must be a Character response.")
            return

        self._streaming = True
        self._stream_speaker = self.state.character_name.strip() or "Character"
        self._stream_buffer = ""
        self._set_generation_controls_enabled(False)
        self._set_llm_busy("Regenerating response...")

        thread = threading.Thread(target=self._redo_stream_worker, daemon=True)
        thread.start()
        self.root.after(50, self._poll_stream_queue)

    def _redo_stream_worker(self) -> None:
        try:
            response_text = self.controller.redo_response(
                stream=True,
                on_stream_token=lambda chunk: self._stream_queue.put(("chunk", chunk)),
            )
            self._stream_queue.put(("done", response_text))
        except Exception as exc:
            self._stream_queue.put(("error", str(exc)))

    def _on_make_summary(self) -> None:
        if self._streaming or self._summary_running:
            return

        self._push_fields_to_state()
        self._summary_running = True
        self._set_generation_controls_enabled(False)
        self._set_llm_busy("Building summary...")

        thread = threading.Thread(target=self._summary_worker, daemon=True)
        thread.start()
        self.root.after(50, self._poll_stream_queue)

    def _summary_worker(self) -> None:
        try:
            summary = self.controller.make_summary()
            self._stream_queue.put(("summary_done", summary))
        except Exception as exc:
            self._stream_queue.put(("summary_error", str(exc)))

    def _on_delete_last_message(self) -> None:
        if self._streaming or self._summary_running:
            return
        self._push_fields_to_state()
        self.controller.delete_last_message()
        self.refresh_chat_history()
        self.update_token_monitor()

    def _on_stop_generation(self) -> None:
        self.controller.stop_generation()

    def _on_save_game(self) -> None:
        self._push_fields_to_state()
        path = filedialog.asksaveasfilename(
            title="Save Game",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as file_obj:
                json.dump(self.state.to_dict(), file_obj, ensure_ascii=False, indent=2)
        except OSError as exc:
            messagebox.showerror("Save Error", str(exc))

    def _on_load_game(self) -> None:
        if self._streaming or self._summary_running:
            return

        path = filedialog.askopenfilename(
            title="Load Game",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        try:
            loaded_state = GameState.from_dict(payload)
        except ValueError as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        self.state = loaded_state
        self.controller.state = self.state
        self._apply_state_to_widgets()
        self.refresh_chat_history()
        self.update_token_monitor()

    def _apply_state_to_widgets(self) -> None:
        self.player_name_var.set(self.state.player_name)
        self.character_name_var.set(self.state.character_name)

        self.player_description_text.delete("1.0", tk.END)
        self.player_description_text.insert("1.0", self.state.player_description)

        self.character_description_text.delete("1.0", tk.END)
        self.character_description_text.insert("1.0", self.state.character_description)

        self.world_scenario_text.delete("1.0", tk.END)
        self.world_scenario_text.insert("1.0", self.state.world_scenario)

        self.story_intent_text.delete("1.0", tk.END)
        self.story_intent_text.insert("1.0", self.state.story_intent)

        self.scene_memory_text.delete("1.0", tk.END)
        self.scene_memory_text.insert("1.0", self.state.scene_memory)

        self.temperature_var.set(str(self.state.settings.get("temperature", DEFAULT_SETTINGS["temperature"])))
        self.top_p_var.set(str(self.state.settings.get("top_p", DEFAULT_SETTINGS["top_p"])))
        self.presence_penalty_var.set(
            str(self.state.settings.get("presence_penalty", DEFAULT_SETTINGS["presence_penalty"]))
        )
        self.frequency_penalty_var.set(
            str(self.state.settings.get("frequency_penalty", DEFAULT_SETTINGS["frequency_penalty"]))
        )
        self.max_tokens_var.set(str(self.state.settings.get("max_tokens", DEFAULT_SETTINGS["max_tokens"])))
        self.prompt_debug_var.set(
            bool(self.state.settings.get("prompt_debug", DEFAULT_SETTINGS["prompt_debug"]))
        )
        loaded_base_url = self.controller.set_llm_base_url(
            str(self.state.settings.get("llm_base_url", self.controller.get_default_llm_base_url()))
        )
        self.state.settings["llm_base_url"] = loaded_base_url
        self.llm_base_url_var.set(loaded_base_url)
        loaded_context_limit = self._safe_int(
            str(self.state.settings.get("context_limit", self.controller.get_memory_limit())),
            self.controller.get_memory_limit(),
        )
        self.controller.set_memory_limit(loaded_context_limit)
        self.memory_limit_var.set(str(loaded_context_limit))

    def _set_generation_controls_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.send_button.configure(state=state)
        self.redo_button.configure(state=state)
        self.summary_button.configure(state=state)
        self.delete_last_button.configure(state=state)
        self.save_button.configure(state=state)
        self.load_button.configure(state=state)
        self.stop_button.configure(state=tk.NORMAL)

    def _set_llm_busy(self, message: str) -> None:
        self.llm_status_var.set(f"LLM: {message}")
        self.llm_progress.start(10)

    def _set_llm_idle(self) -> None:
        self.llm_status_var.set("LLM: Idle")
        self.llm_progress.stop()

    def refresh_chat_history(self, transient_turn: tuple[str, str] | None = None) -> None:
        chat_history_text = self.controller.get_chat_history_text() if self.state.chat_history else ""
        if transient_turn is not None and transient_turn[1]:
            transient_text = f"{transient_turn[0]}: {transient_turn[1]}"
            chat_history_text = f"{chat_history_text}\n\n{transient_text}" if chat_history_text else transient_text

        self.chat_history_text.configure(state=tk.NORMAL)
        self.chat_history_text.delete("1.0", tk.END)
        self.chat_history_text.insert("1.0", chat_history_text)
        self.chat_history_text.configure(state=tk.DISABLED)
        self.chat_history_text.see(tk.END)

    def update_token_monitor(self) -> None:
        self._push_fields_to_state()

        used_tokens, max_tokens = self.controller.preview_context_tokens(
            user_input=self._read_text(self.message_input_text),
        )

        self.context_tokens_var.set(f"Context tokens: {used_tokens} / {max_tokens}")
        self.last_request_var.set(f"Last request: {self._last_request_tokens} tokens")

        ratio = 0.0 if max_tokens <= 0 else used_tokens / max_tokens
        if ratio < 0.6:
            color = "green"
        elif ratio < 0.8:
            color = "orange"
        else:
            color = "red"

        self.context_tokens_label.configure(foreground=color)

        if self.state.settings.get("prompt_debug", False):
            signature = (
                used_tokens,
                max_tokens,
                len(self.state.chat_history),
            )
            if signature != self._last_prompt_debug_signature:
                logger.info(
                    "Prompt Debug - tokens: %s/%s, chat_turns=%s",
                    used_tokens,
                    max_tokens,
                    signature[2],
                )
                self._last_prompt_debug_signature = signature
        else:
            self._last_prompt_debug_signature = None

    def run(self) -> None:
        self.root.mainloop()
