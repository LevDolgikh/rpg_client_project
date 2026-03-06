# RPG Chat Client (v2.01)

Desktop `tkinter` app for roleplay chat with local LLMs via LM Studio (OpenAI-compatible API).

This is a hobby project for personal use and it is not deeply tested.
Quality and stability depend heavily on the selected language model and prompt behavior.

Runtime architecture:
- `user` = Player
- `assistant` = Character
- After `Send Message`, Character response starts automatically in streaming mode

## Model Compatibility

- Reasoning/thinking models are not supported.
- Tested with `Llama 3.2 3B Instruct`.

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
- Streaming generation with cancellation
- LLM activity indicator in `Controls` (`LLM: ...` + progress bar)
- Configurable `LM Studio URL` in UI + `Reset Default URL`
- Context token monitor
- Save/Load game state as JSON (`version: 2`)
- Strict load validation for schema `version: 2`

## Requirements

- Python 3.10+
- LM Studio with a loaded chat model
- Python packages:
  - `requests`
  - `tiktoken` (optional, improves token counting accuracy)

## Quick Start

```bash
pip install -r requirements.txt
python src/main.py
```

Default LM Studio URL is `http://127.0.0.1:1234` and can be changed in `Server Status`.

## How to Use

1. Fill names and context (especially `World Description` and `Story Intent`).
2. (Optional) Set `LM Studio URL` in `Server Status`.
3. Enter a player message in `Message Input`.
4. Click `Send Message`.
5. Use `Redo Response` to regenerate the latest Character response.
6. Use `Make Summary` to summarize older chat turns and append the result to `Scene Memory`.

## Save Format

Only `version: 2` is supported.

Key fields:
- `player_name`, `character_name`
- `player_description`, `character_description`
- `world_scenario` (shown in UI as `World Description`)
- `story_intent`
- `scene_memory`
- `chat_history`: array of `{ "speaker": "player|character", "text": "..." }`
- `settings` (includes generation settings, `context_limit`, `llm_base_url`)

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
  LICENSE
  README.md
  requirements.txt
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

- `LM Studio: Disconnected`: check that LM Studio server is running and that `LM Studio URL` is correct.
- `Load Error`: save file does not match strict schema `version: 2`.
- High context usage: shorten context fields and use `Make Summary`.
