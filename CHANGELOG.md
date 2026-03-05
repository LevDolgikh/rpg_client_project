# Changelog

All notable project changes are recorded here.

This file follows a simple Keep a Changelog style with versioned releases.

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
