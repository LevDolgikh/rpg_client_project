# RPG Chat Client

Desktop app on `tkinter` for roleplay chat with OpenAI-compatible LLM servers.

Current release: **v3.0.1**

## What Changed in v3

- Project was rebuilt manually with a simplified architecture.
- Added cloud LLM support (in addition to local providers).
- Streaming response mode is enabled by default for lower perceived latency.
- Connection and generation flows were cleaned up and stabilized.

## Features

- OpenAI-compatible backend support via configurable URL and API key.
- Provider presets:
  - LM Studio (Local)
  - Ollama (Local)
  - OpenAI (Cloud)
- Model list loading and active model selection.
- Character/world context fields used as system prompt context.
- Chat actions:
  - Send message
  - Regenerate last response
- Streaming assistant output in chat (default).
- Save/Load game state as JSON.

## Requirements

- Python 3.10+
- Access to an OpenAI-compatible API endpoint (local or cloud)
- Dependency from `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/main.py
```

## Configuration

In the app UI:

- Choose provider preset or set custom `Server URL`.
- Set API key (optional for local servers).
- Connect and pick model.

Default preset URLs:

- LM Studio: `http://localhost:1234/v1/`
- Ollama: `http://localhost:11434/v1/`
- OpenAI: `https://api.openai.com/v1/`

## Project Structure

```text
rpg_client_project/
  CHANGELOG.md
  LICENSE
  README.md
  requirements.txt
  src/
    game.py
    llm_client.py
    main.py
    settings.py
    ui.py
```
