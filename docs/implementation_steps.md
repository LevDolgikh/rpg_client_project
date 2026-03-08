# Implementation Steps for v3.00 Migration

This document breaks down the migration guide into concrete development phases and subtasks.

## Overview
The migration to v3.00 transitions the RPG Chat Client from a local LM Studio-only backend to a modular, multi-provider architecture supporting both local and cloud LLMs. The work will occur in clearly defined phases, each building on the previous one.

## Phases and Tasks

### Phase 1 – Provider Abstraction
1. Create a new `providers` package or module (e.g. `providers/__init__.py`).
2. Define an abstract base class `LLMProvider` with the methods `connect`, `disconnect`, `list_models`, `generate`, and `generate_stream`.
3. Implement `LocalProvider` wrapping the existing `llm_client.py` logic (LM Studio / Ollama local server).
4. Update `chat_controller.py` to depend on an `LLMProvider` instance rather than `LLMClient` directly.
5. Add provider selection to `models.py` settings but default to local.

### Phase 2 – UI Connection Selector
1. Update `ui.py` to add new fields in the Server Status section:
   - Connection Type dropdown (Local / OpenAI / Ollama Cloud)
   - Server URL input
   - API Key input (password style)
   - Model dropdown (populated after connect)
   - Connect & Disconnect buttons
2. Ensure the connect flow is manual and triggers provider.connect().
3. Display connection status messages (Disconnected/Connecting/Connected).
4. Disable irrelevant fields when disconnected (e.g. model selector).

### Phase 3 – OpenAI Provider ✅
1. Implement `OpenAIProvider` subclass of `LLMProvider`. (done)
2. Handle base_url, authorization headers, and model naming. (done)
3. Ensure `generate` and `generate_stream` work with OpenAI API semantics. (done)
4. Add any necessary normalization for streaming responses. (done)

*Provider can now be selected and configured via the UI; connection logic performs authentication check and model listing.*

### Phase 4 – Ollama Cloud Provider ✅
1. Implement `OllamaCloudProvider` subclass. (done)
2. Adapt to `api.ollama.com` endpoints and any differences. (done)

*Provider behaves like OpenAI variant with identical API shape; UI supports switching and model enumeration.*

### Phase 5 – Settings Extension ✅
1. Extend `models.py` to store `provider`, `llm_base_url`, `api_key`, `model`, and other new options with defaults. (done)
2. Ensure API keys are saved only in memory and not persisted to disk or logs. (done via `to_dict`/`from_dict` sanitization)
3. Update save/load routines if needed for backward compatibility (should be none). (existing code already merges and backfills)

### Phase 6 – Connection Feedback and Errors ✅
1. Improve the status indicator with clear messages and progress. (added busy messages, progress bar, detailed status text)
2. Show errors from failed connections or model listing. (UI now displays dialogs and includes exception details)
3. Ensure API keys are never logged or exposed. (no logging of keys, UI hides them)

*All phases through 6 have been implemented and tested manually via code snippets.*

## Additional Notes
- Throughout the implementation, keep game mechanics untouched.
- Maintain backward compatibility: existing save files should load without change.
- UI/Controller tests should be updated to exercise the new provider abstraction.


> **Next Step**: Wait for user command before starting implementation. The real work will proceed step‑by‑step following these phases.