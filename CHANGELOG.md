# Changelog

All notable project changes are recorded here.

## [3.00] - 2026-03-08 (unreleased)

### Added
- Provider abstraction layer and `providers` package supporting multiple LLM backends.
- New `OpenAIProvider` and `OllamaCloudProvider` implementations.
- UI connection selector with manual "Connect" / "Disconnect" workflow.
- Fields for Connection Type, Server URL, API Key, and dynamic Model dropdown.
- Factory `get_provider` and controller helpers for swapping providers.
- Settings extended with `provider`, `model`, `api_key` (non-persisted), and `llm_base_url`.
- Provider-specific configuration methods (base_url, api_key, model). 
- Automatic model listing after successful connection with dropdown population.
- Status feedback improvements: busy indicator, error dialogs, model-specific status.

### Changed
- Refactored `ChatController` to use generic `LLMProvider` rather than `LLMClient`.
- `ui.py` rewritten extensively for connection UI, provider settings, and layout adjustments.
- `models.py` settings schema extended while preserving backward compatibility.
- API keys are excluded from save files and logs.

### Security
- API keys stored only in runtime memory and never written to disk or shown in UI.

### Notes
- Local provider support remains identical; new cloud providers are optional.

## [2.01] - 2026-03-06

### Notes
- This release is primarily a bug-fix pass for issues introduced by the migration shipped in `2.00`.

### Changed
- Normalized character responses to a single paragraph in `src/chat_controller.py` by collapsing newline characters into spaces and trimming duplicate whitespace.
- Applied the same normalization to transient streaming text in `src/ui.py`, so streamed output no longer shows multi-line paragraph breaks before final save.
- Removed `Max Tokens` setting from `src/ui.py`, `src/chat_controller.py`, `src/models.py`, and `src/llm_client.py` due to inconsistent behavior; response length is now controlled only by prompt/model behavior.
- Removed the unused hidden `max_chat_messages` limiter from `src/context_builder.py` to keep trimming strictly token-limit based.
- Added persistent context limit setting `context_limit` in `src/models.py` and synchronized it in `src/ui.py`, so `Memory Limit` now survives save/load and is applied on startup.
- Changed summary behavior in `src/chat_controller.py`: `Make Summary` now appends to existing `Scene Memory` instead of replacing it.
- Added visible LLM activity indicator in `src/ui.py` (`LLM: ...` status + indeterminate progress bar) during response generation, redo, and summary.
- Moved summary execution in `src/ui.py` to a background worker with queue polling, so the UI no longer appears frozen while summary is being generated.
- Added configurable LM Studio connection URL in `src/ui.py` (`LM Studio URL`) with `Reset Default URL`, and wired persistence/apply flow through `src/models.py`, `src/chat_controller.py`, and `src/llm_client.py`.
- Refreshed `README.md` for release accuracy (new URL workflow, summary behavior, activity indicator, updated quick start and structure).
- Added `LICENSE` and `requirements.txt` for GitHub release packaging.

## [2.00] - 2026-03-06

### Changed
- Migrated the app to the role-invariant architecture: `player -> character` with fixed role mapping (`user`/`assistant`).
- Removed manual speaker routing and switched chat flow to automatic character generation immediately after `Send Message`.
- Reworked context model: merged legacy intent fields into a single `story_intent` and clarified world context as `World Description` in UI.
- Switched chat history to canonical turn objects (`{speaker, text}`) across runtime, prompt building, summaries, and persistence.
- Tightened save/load contract to strict schema `version: 2` with explicit validation errors.

### Removed
- Removed `Enhance Message` feature.
- Removed legacy role-switching controls (`Speaker`, `Generate Response`).
- Removed migration documentation folder `docs/` after completion.

### Notes
- Migration image: project moved from a manual gearbox to an automatic transmission - fewer levers, steadier motion.

## [1.02] - 2026-03-06

### Changed
- Refactored `src/prompts.py` to remove duplicated LLM roleplay rules by extracting shared text into `COMMON_ROLEPLAY_RULES` and reusing it in `SYSTEM_PROMPT` and `ENHANCE_PROMPT`.
- Improved `Chat History` readability in `src/ui.py` and `src/chat_controller.py` by rendering chat turns with a blank line separator between messages (including transient streaming output).
- Fixed clipboard shortcuts in `src/ui.py` for non-English keyboard layouts (including Russian), so `Ctrl+C/X/V/A` works reliably in text fields.
- Added undo/redo keyboard support in editable text fields: `Ctrl+Z` (undo) and `Ctrl+Y` (redo), with non-English layout handling in `src/ui.py`.
- Fixed `Enhance Message` flow in `src/chat_controller.py`/`src/ui.py` so rewriting now uses selected speaker, current context fields, and trimmed recent chat history instead of rewriting in isolation.

## [1.01] - 2026-03-05

### Added
- Added `.gitignore` entries for Python bytecode cache files under `src/__pycache__/`.
- Added changelog workflow guidance and `CHANGELOG.md` reference to `README.md`.

### Changed
- Updated `ENHANCE_PROMPT` in `src/prompts.py` to enforce the same roleplay style and formatting rules as the main system prompt.
- Fixed speaker-role alignment in `src/context_builder.py` so generation now builds the system prompt for the selected next speaker.
- Added advanced option guidance in `src/ui.py`, including inline parameter explanations, a "Reset Recommended" button, and a Prompt Debug Mode usage hint.
- Improved Prompt Debug Mode logging in `src/ui.py` by emitting prompt token stats at INFO level with de-duplication.
- Unified generation defaults with `DEFAULT_SETTINGS` in `src/models.py` and applied them across UI/controller.
- Tuned roleplay defaults for local models: `temperature=0.7`, `top_p=0.9`, `presence_penalty=0.3`, `frequency_penalty=0.2`, `max_tokens=120`.
- Enforced safe generation ranges in both `src/ui.py` and `src/chat_controller.py`.
