from __future__ import annotations

import logging
import tkinter as tk

from chat_controller import ChatController
from context_builder import ContextBuilder
from memory_manager import MemoryManager
from providers import LocalProvider
from models import GameState
from token_manager import TokenManager
from ui import RPGChatUI


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    state = GameState()
    token_manager = TokenManager(max_tokens=4096)
    context_builder = ContextBuilder(token_manager=token_manager)
    # start with a local provider by default
    provider = LocalProvider()
    memory_manager = MemoryManager(llm_client=provider)

    controller = ChatController(
        state=state,
        context_builder=context_builder,
        provider=provider,
        memory_manager=memory_manager,
    )

    root = tk.Tk()
    app = RPGChatUI(root=root, controller=controller, state=state)
    app.run()


if __name__ == "__main__":
    main()
