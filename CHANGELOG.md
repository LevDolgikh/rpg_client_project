# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [3.0.1] - 2026-03-12

### Changed
- Add token limit

## [3.0.0] - 2026-03-11

### Changed
- Rebuilt the application architecture around a simplified codebase:
  - `ui.py` (Tkinter interface)
  - `game.py` (application service layer)
  - `llm_client.py` (OpenAI-compatible transport)
  - `settings.py` (prompt and provider defaults)
- Added cloud LLM support through OpenAI-compatible endpoints, including provider presets in UI:
  - LM Studio (local)
  - Ollama (local)
  - OpenAI (cloud)
- Switched generation to streaming by default in the UI for faster first-token feedback.
- Improved connection and generation error handling paths in UI/client interaction.

### Fixed
- Fixed multiple stability issues from earlier versions during the manual rebuild.
- Fixed chat update behavior for incremental assistant output rendering.
- Fixed model selection and reconnect flow edge cases.

## [2.0.1] - 2026-03-06

### Changed
- Stabilization and bug-fix pass for the v2 migration branch.

## [2.0.0] - 2026-03-06

### Changed
- Major architecture migration in the legacy branch (superseded by v3 rebuild).
