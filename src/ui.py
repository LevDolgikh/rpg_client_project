"""GUI of application
"""

# ui
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

# game
from settings import DEFAULT_SETTINGS
from game import RPG_client

# sub
import threading
import json

class RPG_ui(tk.Tk):
    """Main class for the RPG client GUI, responsible for creating and managing the user interface"""

    def __init__(self, rpg_client):
        """Initialize the RPG client GUI and set up the main window and widgets"""
        super().__init__()

        # RPG_client
        self.rpg_client = rpg_client

        # Server default settings
        self.providers = DEFAULT_SETTINGS.BASE_CONNECTION_OPTIONS
        self.providers_names = self.get_default_providers_names(self.providers)
        self.default_provider = self.providers[0]
        self.default_provider_name = self.default_provider['name']
        self.server_url = self.get_server_url(self.default_provider['name'])
        self.api_key = ""

        # Server status
        self.connected = False

        # Server models
        self.model_ids = []

        # Layout
        self.layout()

    def get_default_providers_names(self, providers):
        """Collect information about names from default providers from settings"""
        names = []

        for provider in providers:
            names.append(provider['name'])

        return names
    
    def get_server_url(self, name):
        """Collect information about names from default providers from settings"""
        url = ""
        for provider in self.providers:
            if provider['name'] == name:
                url = provider['base_url']
        return url
    
    def combobox_provider_selected(self, event):
        """Actions per selecting provider: set default server adress"""
        self.server_url = self.get_server_url(event.widget.get())
        self.entry_server_URL.delete(0, tk.END)
        self.entry_server_URL.insert(0, self.server_url)

    def combobox_model_selected(self, event):
        """Actions per selecting model: set model"""
        model_selected = event.widget.get()
        self.set_model(model_selected)

    def set_model(self, model_id):
        res = self.rpg_client.set_active_model(model_id)
        if res:
            status = "Connected(" + model_id +")"
            self.label_connection.config(text = status)
        else:
            self.disconnect()
            self.label_connection.config(text = "Disconnected. Model selection error")

    def _generate_worker(self):

        res = self.rpg_client.generate_responce(self.entry_character.get(),
                                                self.text_char.get("1.0", "end-1c"),
                                                self.text_world.get("1.0", "end-1c"),
                                                self.text_chat.get("1.0", "end-1c"))
        self.after(0, self._generate_finished, res)
    
    def _generate_finished(self, res):

        self.button_send.config(state="normal")
        self.button_regen.config(state="normal")

        if res:
            self.label_generation.config(text="Generation Done")
            self.text_chat.insert(tk.END, res)
        else:
            self.label_generation.config(text="Generation Error")

    def _connect_worker(self):

        res = self.rpg_client.connect_to_llm(self.server_url, self.api_key)

        self.after(0, self._connect_finished, res)
    
    def _connect_finished(self, res):

        if res:
            # server entry block off
            self.button_disconnect.config(state = "normal")
            self.connected = True
            self.label_connection.config(text="Connected")
            self.entry_server_URL.config(state="readonly")
            self.entry_api.config(state="readonly")
            
            # Models update
            self.model_ids = res
            self.combobox_model.config(state = "readonly")
            self.combobox_model.config(values=self.model_ids)
            self.combobox_model.current(0)
            self.set_model(self.model_ids[0])

            # generation buttons
            self.button_send.config(state='normal')
            self.button_regen.config(state='normal')
        else:
            self.disconnect()
            self.label_connection.config(text='Connection Error')

    def connect(self):
        
        self.button_connect.config(state="disabled")
        self.button_disconnect.config(state="disabled")
        self.label_connection.config(text="Processing")

        threading.Thread(
            target=self._connect_worker,
            daemon=True
        ).start()
        
    def disconnect(self):

        #server frame update
        self.connected = False
        self.rpg_client.disconnect_from_llm()
        self.label_connection.config(text='Disconnected')
        self.entry_server_URL.config(state = 'normal')
        self.entry_api.config(state = 'normal')
        self.button_connect.config(state="normal")

        # models update
        self.combobox_model.config(state = "disabled")
        self.model_ids = []

        # generation buttons update
        self.button_send.config(state='disabled')
        self.button_regen.config(state='disabled')

    def generate(self):

        self.button_send.config(state="disabled")
        self.button_regen.config(state="disabled")
        self.label_generation.config(text="Generating")

        user_text = self.text_user_message.get("1.0", "end-1c")
        player_name = self.entry_player.get()
        user_message = player_name + ": " + user_text
        self.text_user_message.delete("1.0", tk.END)
        self.text_chat.insert(tk.END, user_message)

        threading.Thread(
            target=self._generate_worker,
            daemon=True
        ).start()
    
    def regen(self):
        self.label_generation.config(text="Sorry not implemented yet")
        return True
    
    def save_game(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save as"
        )
        if not file_path:
            return
        
        data = {
            "server_url": self.entry_server_URL.get(),
            "server_api": self.entry_api.get(),
            "char_name": self.entry_character.get(),
            "player_name": self.entry_player.get(),
            "char_disc": self.text_char.get("1.0", "end-1c"),
            "world_disc": self.text_world.get("1.0", "end-1c"),
            "chat": self.text_chat.get("1.0", "end-1c")
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.label_save_load.config(text = "Game Ssuccessfully Saved")
        except Exception as e:
            self.label_save_load.config(text = "Save Error")
                
        
    def load_game(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load from"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Заполняем поля
            self.entry_server_URL.delete(0, tk.END)
            self.entry_server_URL.insert(0, data.get("server_url", ""))

            self.entry_api.delete(0, tk.END)
            self.entry_api.insert(0, data.get("server_api", ""))

            self.entry_character.delete(0, tk.END)
            self.entry_character.insert(0, data.get("char_name", ""))

            self.entry_player.delete(0, tk.END)
            self.entry_player.insert(0, data.get("player_name", ""))

            self.text_char.delete("1.0", tk.END)
            self.text_char.insert("1.0", data.get("char_disc", ""))

            self.text_world.delete("1.0", tk.END)
            self.text_world.insert("1.0", data.get("world_disc", ""))

            self.text_chat.delete("1.0", tk.END)
            self.text_chat.insert("1.0", data.get("chat", ""))

            self.label_save_load.config(text = "Game successfully loaded")
        except FileNotFoundError:
            self.label_save_load.config(text = "File Not Found")
        except json.JSONDecodeError:
            self.label_save_load.config(text = "Save file wrong format")
        except Exception as e:
            self.label_save_load.config(text = "Load Error")

    def layout(self):
        
        # Window settings
        self.title("RPG chat client")
        self.geometry("800x600")

        frame_global = tk.Frame(self)
        frame_global.pack(side="top", pady=20)

        # Server frame
        frame_server = tk.LabelFrame(frame_global, text = "Server Information")
        frame_server.grid(row=0, column=0, padx=5, pady=5, columnspan=3)

        label_provider = tk.Label(frame_server, text="Provider:")
        label_provider.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.combobox_provider = ttk.Combobox(frame_server, values = self.providers_names, state = "readonly")
        self.combobox_provider.set(self.default_provider_name)
        self.combobox_provider.bind("<<ComboboxSelected>>", self.combobox_provider_selected)
        self.combobox_provider.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        label_api = tk.Label(frame_server, text="Presets")
        label_api.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        label_server_URL = tk.Label(frame_server, text="Server URL:")
        label_server_URL.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.entry_server_URL = tk.Entry(frame_server, width = 40)
        self.entry_server_URL.insert(0, self.server_url)
        self.entry_server_URL.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        label_api = tk.Label(frame_server, text="Example: https://api.openai.com/v1/ (OpenAI Compatible only)")
        label_api.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        label_api = tk.Label(frame_server, text="API key")
        label_api.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.entry_api = tk.Entry(frame_server, width= 40)
        self.entry_api.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        label_api = tk.Label(frame_server, text="Leave this blank for local models")
        label_api.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Server buttonss
        frame_server_buttons = tk.Frame(frame_server)
        frame_server_buttons.grid(row=3, column=0, padx=5, pady=5, columnspan=3, sticky= 'w')

        self.button_connect = tk.Button(frame_server_buttons, 
                                        text="Connect",
                                        command=self.connect,
                                        width = 20
        )
        self.button_connect.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.button_disconnect = tk.Button(frame_server_buttons, 
                                text="Disconnect",
                                command=self.disconnect,
                                width = 20
        )
        self.button_disconnect.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.label_connection = tk.Label(frame_server_buttons, text="Disconnected")
        self.label_connection.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # World and character settings frame
        frame_world_character = tk.LabelFrame(frame_global, text = "World and Character Settings", width=100)
        frame_world_character.grid(row=1, column=0, padx=5, pady=5, columnspan=3)

        label_model = tk.Label(frame_world_character, text="Model:")
        label_model.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.combobox_model = ttk.Combobox(frame_world_character, values = self.model_ids, state = "disabled")
        self.combobox_model.bind("<<ComboboxSelected>>", self.combobox_model_selected)
        self.combobox_model.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        label_character_name = tk.Label(frame_world_character, text="Character name:")
        label_character_name.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        self.entry_character= tk.Entry(frame_world_character)
        self.entry_character.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        label_player_name = tk.Label(frame_world_character, text="Player name:")
        label_player_name.grid(row=4, column=0, padx=5, pady=5, sticky="w")

        self.entry_player= tk.Entry(frame_world_character)
        self.entry_player.grid(row=5, column=0, padx=5, pady=5, sticky="w")

        label_world = tk.Label(frame_world_character, text="World Information and Scenario")
        label_world.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.text_world = tk.Text(frame_world_character, height=10, width=31)
        self.text_world.grid(row=1, column=1, padx=5, pady=5, sticky="w", rowspan= 6)
        
        label_char = tk.Label(frame_world_character, text="Character Information")
        label_char.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.text_char = tk.Text(frame_world_character, height=10, width=31)
        self.text_char.grid(row=1, column=2, padx=5, pady=5, sticky="w", rowspan= 6)

        # Chat section
        frame_chat= tk.LabelFrame(frame_global, text = "Chat")
        frame_chat.grid(row=2, column=0, padx=5, pady=5, columnspan=3)

        self.text_chat = tk.Text(frame_chat, height=8, width=83)
        self.text_chat.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        label_user_message = tk.Label(frame_chat, text="Your message")
        label_user_message.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.text_user_message = tk.Text(frame_chat, height=4, width=83)
        self.text_user_message.grid(row=2, column=0, padx=5, pady=5, sticky="w")

        #  Chat and save/load controls
        frame_chat_buttons = tk.Frame(frame_chat)
        frame_chat_buttons.grid(row=3, column=0, padx=5, pady=5, columnspan=3, sticky= 'w')

        self.button_send = tk.Button(frame_chat_buttons, 
                                     text="Send message",
                                     command=self.generate,
                                     width = 20,
                                     state="disabled"
        )
        self.button_send.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.button_regen = tk.Button(frame_chat_buttons, 
                                text="Regenerate last",
                                command=self.regen,
                                width = 20,
                                state="disabled"
        )
        self.button_regen.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.label_generation = tk.Label(frame_chat_buttons, text="Send message to start")
        self.label_generation.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Chat controls
        self.button_save = tk.Button(frame_chat_buttons, 
                                     text="Save game",
                                     command=self.save_game,
                                     width = 20,    
                                     state="normal"
        )
        self.button_save.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.button_load = tk.Button(frame_chat_buttons, 
                                text="Load game",
                                command=self.load_game,
                                width = 20,
                                state="normal"
        )
        self.button_load.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.label_save_load = tk.Label(frame_chat_buttons, text="")
        self.label_save_load.grid(row=1, column=2, padx=5, pady=5, sticky="w")

       

if __name__ == "__main__":
    """Test of GUI"""

    # Init
    rpg_client = RPG_client()
    app = RPG_ui(rpg_client)

    # providers name test
    provider_names = app.get_default_providers_names(DEFAULT_SETTINGS.BASE_CONNECTION_OPTIONS)
    print(provider_names)

    app.mainloop()

