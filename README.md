# RPG Chat Client

Desktop tkinter application for roleplay chat with local LLM models through LM Studio (OpenAI-compatible API).

The project is optimized for small local models (~3B parameters) and short context windows (2048-4096 tokens).

Primary tested LLM model: `Llama 3.2 3B Instruct`.

The application is not designed or validated for reasoning-focused models (`thinking` models): they typically produce significantly longer responses and have less predictable token consumption, which can degrade UX and context budgeting behavior.

## Features

- Roleplay chat with `Player` and `Character` turns
- Context fields for persona, goals, world state, direction, and scene memory
- Manual summarization of old chat into scene memory (`Make Summary`)
- Token monitor for current context usage
- Streaming generation with cancellation (`Stop Generation`)
- Save/load full game state as JSON
- Turn text normalization to avoid duplicated speaker prefixes
- Clipboard shortcuts in editable text fields

## Requirements

- Python 3.10+
- LM Studio running locally with a loaded chat model
- LM Studio local server enabled at `http://127.0.0.1:1234`
- Python packages:
  - `requests`
  - `tiktoken` (optional, fallback estimator is used if unavailable)

## Quick Start

1. Install dependencies:

```bash
pip install requests tiktoken
```

2. Start LM Studio local server and load your model.
3. Run the app from project root:

```bash
python src/main.py
```

## How It Works

1. Fill in names and context fields (`Character Description`, `World Scenario`, `Story Direction`, etc.).
2. Choose speaker in `Message Input` and send or generate turns.
3. Use `Make Summary` to compress older messages into `Scene Memory`.
4. Use `Save Game` / `Load Game` to persist and restore sessions.

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
  docs/
    architecture.md
    coding_rules.md
    context_builder_design.md
    implementation_spec.md
    llm_generation_prompt.md
    product_spec.md
    prompts_spec.md
    ui_layout_spec.md
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

- `LM Studio: Disconnected`: confirm LM Studio server is running and reachable at `http://127.0.0.1:1234`.
- Generation errors: verify a model is loaded in LM Studio and supports chat completions.
- High token usage: shorten context fields and summarize old chat.

## Documentation

Detailed design and implementation specs are in `docs/`:

- `product_spec.md`
- `architecture.md`
- `implementation_spec.md`
- `prompts_spec.md`
- `context_builder_design.md`
- `ui_layout_spec.md`
- `coding_rules.md`

## Change Tracking

Use `CHANGELOG.md` for incremental project updates and behavior changes.

As a default workflow, add a changelog entry for new changes instead of updating spec docs on every small iteration.
