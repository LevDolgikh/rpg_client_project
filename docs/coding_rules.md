# RPG Chat Client
Coding Rules

Version: 1.0


# 1. Purpose

This document defines coding rules for implementing the RPG Chat Client.

The goal is to ensure:

• clean architecture
• modular code
• predictable LLM-generated code
• maintainability


These rules must always be followed during development.


# 2. Programming Language

Language: Python

Required version:

Python 3.10 or newer.


# 3. Allowed Libraries

Standard library.

External libraries:

requests

tiktoken (optional)


GUI framework:

tkinter


No additional dependencies should be introduced without clear need.


# 4. File Size Limits

Source files should remain reasonably small.

Recommended limit:

500 lines per file.

If a file grows too large, logic must be refactored into separate modules.


# 5. Separation of Responsibilities

UI must never contain business logic.

UI responsibilities:

• rendering interface
• collecting input
• displaying output


Application logic belongs in controller modules.


# 6. Data Model Rules

All session data must be stored in a single object:

GameState


GameState is the single source of truth for the application.


GameState must contain:

player_name
character_name

player_description
character_description

character_goal

world_scenario

story_direction

scene_memory

chat_history

settings


GameState must support JSON serialization.


# 7. Chat History Format

Chat history must be stored as a list.

Example:


[
 ("Player", "Hello"),
 ("Character", "The guard watches you carefully.")
]


This format simplifies context building.


# 8. Prompt Management

All prompt templates must exist in:

src/prompts.py


Prompts must never be duplicated across modules.


Modules must import prompts from prompts.py.


# 9. Context Construction

All prompt assembly must be handled by:

ContextBuilder


Other modules must never construct prompts directly.


# 10. Token Handling

Token estimation must be handled by:

TokenManager


Two modes must be supported:

tiktoken installed

fallback estimator


Fallback rule:

1 token ≈ 4 characters


# 11. LLM Communication

All communication with the language model must be handled by:

LLMClient


No other module should call the API directly.


# 12. Error Handling

The system must handle common failures:

LM Studio not running

network errors

request timeout

invalid responses


Errors must be reported clearly to the user.


# 13. Streaming Responses

The LLMClient must support streaming responses.

Generated tokens should appear progressively in the UI.

Users must be able to cancel generation.


# 14. Save and Load

Game state must be saved as JSON files.

Save workflow:

GameState → dict → JSON file


Load workflow:

JSON → dict → GameState


# 15. Code Style

The following practices must be used:

type hints for function parameters

clear method names

small functions with single responsibility

descriptive variable names


Avoid deeply nested logic.


# 16. Comments

Code should contain concise comments explaining:

non-obvious logic

important design decisions


Avoid excessive commenting.


# 17. Logging

The application should use the logging module.

Logging should be used for:

API communication

errors

important system events


# 18. Extensibility

The architecture should allow future extension without large refactoring.

Examples of possible extensions:

multi-character roleplay

advanced memory systems

different LLM backends


# 19. Chat Turn Normalization

When saving chat turns, store speaker metadata separately from text.

Message text should be normalized to avoid duplicated leading labels such as
`Player:` or `Character:` in the text body.

Load-time parsing should apply the same normalization for compatibility with
older JSON saves.
