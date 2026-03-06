# RPG Chat Client (v2.00)

Desktop tkinter app for roleplay chat with local LLMs via LM Studio (OpenAI-compatible API).

Runtime architecture:
- `user` = Player
- `assistant` = Character
- After `Send Message`, Character response starts automatically (streaming)

## Model Compatibility

- Reasoning / thinking models are not supported.
- The app was tested with `Llama 3.2 3B Instruct`.

## Features

- Canonical dialogue flow: `player -> character`
- Context fields:
  - `Player Description`
  - `Character Description`
  - `World Description`
  - `Story Intent`
  - `Scene Memory`
- Chat controls:
  - `Send Message`, `Redo Response`
  - `Stop Generation`, `Delete Last Message`, `Make Summary`
- Save/Load game state as JSON (`version: 2`)
- Strict load validation: only save schema v2 is accepted
- Context token monitor
- Streaming generation with cancellation

## Requirements

- Python 3.10+
- LM Studio with a loaded chat model
- LM Studio Local Server at `http://127.0.0.1:1234`
- Python packages:
  - `requests`
  - `tiktoken` (optional)

## Quick Start

```bash
pip install requests tiktoken
python src/main.py
```

## How to Use

1. Fill names and context (especially `World Description` and `Story Intent`).
2. Enter a player message in `Message Input`.
3. Click `Send Message`.
4. The app appends Player turn and immediately generates Character turn.
5. Use `Redo Response` to regenerate the latest Character response.
6. Use `Make Summary` to compress old turns into `Scene Memory`.

## Save Format

Only `version: 2` is supported.

Key fields:
- `player_name`, `character_name`
- `player_description`, `character_description`
- `world_scenario` (shown in UI as `World Description`)
- `story_intent`
- `scene_memory`
- `chat_history`: array of `{ "speaker": "player|character", "text": "..." }`
- `settings`

## Keyboard Shortcuts (Editable Fields)

- Copy: `Ctrl+C` or `Ctrl+Insert`
- Cut: `Ctrl+X` or `Shift+Delete`
- Paste: `Ctrl+V` or `Shift+Insert`
- Select all: `Ctrl+A`
- Undo: `Ctrl+Z`
- Redo: `Ctrl+Y`

## Project Structure

```text
rpg_client_project/
  CHANGELOG.md
  README.md
  src/
    main.py
    ui.py
    chat_controller.py
    context_builder.py
    token_manager.py
    memory_manager.py
    llm_client.py
    prompts.py
    models.py
```

## Troubleshooting

- `LM Studio: Disconnected`: check that LM Studio server is running and reachable at `http://127.0.0.1:1234`.
- `Load Error`: file does not match strict schema `version: 2`.
- High context usage: shorten context fields and use `Make Summary`.
