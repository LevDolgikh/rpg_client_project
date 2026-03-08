# Migration Guide: Local to Cloud LLMs (v3.00)

This document outlines the planned migration for the RPG Chat Client from using a local LM Studio server to supporting cloud-hosted LLM providers.

The goal is to preserve the existing local workflow while introducing optional cloud providers that offer stronger models and larger context windows.

This transition is the centerpiece of the upcoming v3.00 release.

--------------------------------------------------

OBJECTIVES

1. Primary transition to cloud providers while retaining the ability to connect to a local server.
2. Introduce a connection selector UI so users can choose between local and supported cloud services.
3. Show available model list after connection so user can select the active model.
4. Simplify configuration with sensible defaults per provider while allowing custom API keys and URLs.
5. Require explicit connection action ("Connect" / "Disconnect") instead of automatic connection.
6. Improve connection visibility through a clear status indicator and connection progress.
7. Keep game mechanics unchanged. Only the LLM communication layer is modified.

--------------------------------------------------

ARCHITECTURAL OVERVIEW

The current architecture is already modular and cleanly separated:

ui.py
    UI layer

chat_controller.py
    coordinates UI actions and LLM generation

context_builder.py
    builds prompts and context blocks

memory_manager.py
    handles summarization and scene memory

llm_client.py
    performs API communication

models.py
    stores persistent state and settings

The migration mainly affects:

- llm_client.py
- chat_controller.py
- ui.py
- models.py

The following modules remain mostly unchanged:

- context_builder.py
- memory_manager.py
- prompts.py

--------------------------------------------------

PROVIDER ABSTRACTION

Version 3 introduces a provider abstraction layer.

Instead of assuming a single LM Studio server, the application will support multiple LLM providers through a common interface.

Conceptual architecture:

LLM Provider
    LocalProvider (LM Studio / Ollama)
    OpenAIProvider
    OllamaCloudProvider
    Future providers

All providers must implement the same behavior.

Example conceptual interface:

class LLMProvider:

    connect()
        validates configuration and checks connection

    disconnect()
        closes active connection

    list_models()
        returns list of available models

    generate(messages)
        generates full response

    generate_stream(messages)
        streams response tokens

The UI and ChatController interact only with the provider interface.

--------------------------------------------------

SUPPORTED PROVIDERS (v3.00)

Initial supported providers:

LOCAL

- LM Studio
- Ollama (local server)

CLOUD

- OpenAI
- Ollama Cloud (api.ollama.com)

Future providers may include:

- Anthropic
- Google Gemini
- OpenRouter

--------------------------------------------------

UI CHANGES

The "Server Status" section will be redesigned to support provider selection.

New UI fields:

Connection Type
    dropdown selector

    Local
    OpenAI
    Ollama Cloud

Server URL
    editable text field

API Key
    password-style hidden input field

Model
    dropdown list populated after connection

Buttons:

Connect
Disconnect

Connection must be manual.

--------------------------------------------------

CONNECTION WORKFLOW

1. User selects Connection Type
2. UI loads default parameters
3. User enters API key if required
4. User clicks Connect
5. Client validates connection
6. Available models are requested
7. Model selector becomes active

Status examples:

LLM: Disconnected
LLM: Connecting...
LLM: Connected (model_name)

--------------------------------------------------

MODEL SELECTION

After successful connection the client retrieves models.

Example endpoint:

GET /v1/models

The returned models populate the model dropdown.

Example model list:

gpt-4o
gpt-4o-mini
llama3-70b

The selected model is stored in GameState.settings.

--------------------------------------------------

SETTINGS CHANGES

models.py settings will be extended.

Example settings structure:

DEFAULT_SETTINGS = {

    "provider": "local",

    "llm_base_url": "http://localhost:1234",

    "model": "local-model",

    "api_key": "",

    "temperature": 0.7,
    "top_p": 0.9,
    "presence_penalty": 0.3,
    "frequency_penalty": 0.2,

    "context_limit": 4096
}

API keys are not displayed after entry.

--------------------------------------------------

LLM CLIENT CHANGES

llm_client.py becomes provider-agnostic.

Currently the client assumes OpenAI-compatible API:

/v1/chat/completions

This will remain the base protocol.

Cloud providers differ mainly in:

base_url
authorization headers
model naming

Example header:

Authorization: Bearer API_KEY

The client must inject headers only when needed.

--------------------------------------------------

CHAT CONTROLLER CHANGES

ChatController currently calls LLMClient directly.

In v3 it calls the active provider.

Example concept:

provider.generate(messages)

Streaming logic remains unchanged.

This ensures existing chat flow remains identical.

--------------------------------------------------

SECURITY CONSIDERATIONS

API keys must be protected.

Rules:

API keys must never be printed to logs.

API keys must not appear in UI after entry.

API keys must not be stored in save files.

API keys remain only in memory during runtime.

Game save files remain safe to share.

--------------------------------------------------

BACKWARD COMPATIBILITY

Existing save files remain compatible.

Migration defaults:

provider = "local"

model = "local-model"

llm_base_url remains unchanged.

No save format change is required.

--------------------------------------------------

IMPLEMENTATION PLAN

Recommended development order.

PHASE 1

Introduce provider abstraction layer.
Wrap current LM Studio logic into LocalProvider.

PHASE 2

Add UI connection selector.
Add Connect and Disconnect buttons.
Add model selector.

PHASE 3

Implement OpenAI provider.

PHASE 4

Implement Ollama Cloud provider.

PHASE 5

Extend GameState settings safely.

PHASE 6

Improve connection feedback and error messages.

--------------------------------------------------

EXAMPLE UI LAYOUT

Server Status

Connection Type:   OpenAI

API Key:           *************

Server URL:        https://api.openai.com

Model:             gpt-4o

[ Connect ]   [ Disconnect ]

Status: Connected

--------------------------------------------------

RISKS

API incompatibilities.

Some providers do not perfectly follow OpenAI API format.

Mitigation:
Implement provider-specific wrappers.

Streaming differences.

Some providers use different streaming payloads.

Mitigation:
Normalize streaming output in provider layer.

Cloud latency.

Cloud models may respond slower than local models.

Mitigation:
Keep streaming enabled.

--------------------------------------------------

LONG TERM DIRECTION (v4+)

Possible future features:

multiple characters with independent LLMs

provider failover

automatic context compression

plugin architecture for providers

model benchmarking

--------------------------------------------------

SUMMARY

Version 3.00 transitions the RPG Chat Client from a single local LLM backend to a flexible multi-provider architecture.

Benefits:

access to stronger models
larger context windows
more stable narrative flow
optional cloud usage

Local LLM workflows remain fully supported.