# RPG Chat Client
Context Builder Design

Version: 1.0


# 1. Purpose

This document defines how prompts are constructed before sending them to the LLM.

Correct context assembly is critical for:

• roleplay stability
• efficient token usage
• preventing hallucinations
• maintaining story continuity


The context builder must follow this design strictly.


# 2. Context Goals

The context system must:

• keep prompts short and structured
• prioritize important information
• work with small models (~3B parameters)
• stay within 2048–4096 tokens


Small models perform best with structured short context.


# 3. Context Components

Each request sent to the LLM contains the following components:

System Prompt

Context Block

Recent Chat History

Next Speaker Prefix


Order is important and must not be changed.


# 4. System Prompt

The system prompt defines behavior rules for the model.

Example:

You are roleplaying as {character_name}.

Rules:

Write in third person past tense.

Write exactly one paragraph.

Keep responses moderate in length.

Use "quotes" for dialogue.

Use _underscores_ for thoughts.

Use *asterisks* for sounds.

Do not write dialogue or actions for other characters.

Stay in character.


The system prompt must always appear first.


# 5. Context Block

The context block contains structured roleplay information.

Format:

[Context]

Character Persona:
{character_description}

Player Persona:
{player_description}

Character Goal:
{character_goal}

World Scenario:
{world_scenario}

Story Direction:
{story_direction}

Scene Memory:
{scene_memory}


Each section contains short lines.

Rule:

One line = one idea.


# 6. Chat History

Chat history must be stored as structured message turns.

Each message contains:

speaker
text

Example internal representation:

[
 ("Player", "Hello"),
 ("Character", "The guard watches you carefully.")
]

When building prompts, each message must be converted into OpenAI message format.

Example:

{"role": "user", "content": "Player: Hello"}

{"role": "assistant", "content": "Character: The guard watches you carefully."}

This structure improves roleplay stability for small models.


# 7. Chat History Length

To preserve tokens for small models, only recent messages should be included.

Recommended size:

12–16 messages.

Older messages should be summarized into Scene Memory.

# 8. Context Field Size Limits

To maintain predictable token usage the following limits are recommended.

Player Description:
maximum 6 lines

Character Description:
maximum 6 lines

Character Goal:
maximum 6 lines

World Scenario:
maximum 8 lines

Story Direction:
maximum 8 lines

Scene Memory:
maximum 10 lines

These limits ensure the context remains within safe token budget.


# 9. Next Speaker Prefix

The prompt must end with the next speaker label.

Example:

Player: Hello.

Character:


This tells the model whose response to generate.


# 10. Final Prompt Layout

Example final prompt:

System Prompt


[Context]

Character Persona:
...

Player Persona:
...

Character Goal:
...

World Scenario:
...

Story Direction:
...

Scene Memory:
...


Player: Hello.

Character:


This structure must remain consistent across all requests.


# 11. Token Budget Strategy

For a 4096 token limit, recommended allocation:


System prompt
≈ 100 tokens


Context block
≈ 400–600 tokens


Scene memory
≈ 200 tokens


Chat history
≈ 1000–2000 tokens


Model response
≈ 150 tokens


Remaining tokens act as safety buffer.


# 12. History Trimming Algorithm

When token limits are exceeded:

1 Remove oldest chat messages.

2 Preserve newest messages.

3 Never remove context block.

4 Never remove system prompt.


Priority order:

System prompt

Context block

Scene memory

Recent chat


Chat history is always trimmed first.


# 13. Scene Memory Usage

Scene Memory stores condensed history.

Example:

Player arrived in abandoned town
Character distrusts Player
Strange bell rings every night


Scene Memory replaces long chat history.


This keeps token usage low.


# 14. Summary Workflow

User clicks:

Make Summary


Process:

Old chat messages are selected.

↓

Messages sent to LLM using summary prompt.

↓

LLM returns condensed memory.

↓

Scene Memory is updated.


Old messages may then be removed from chat history.


# 15. Token Estimation

Token estimation must run before sending requests.

Two methods supported:

tiktoken (preferred)

fallback estimation


Fallback rule:

1 token ≈ 4 characters.


# 16. Context Debug Mode

When debug mode is enabled, the system must log context debug data.

Current implementation logs estimated context token count at debug level.


This helps diagnose roleplay issues.


# 17. Turn Text Storage Constraint

The internal `chat_history` turn format remains:

`(speaker, text)`

where `text` should contain message body only, without redundant leading
speaker labels.

If upstream/generated text contains a leading label (for example
`Character: ...`), storage-time normalization should remove the duplicated
prefix before persisting the turn.
