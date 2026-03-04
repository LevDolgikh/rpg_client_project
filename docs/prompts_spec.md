# RPG Chat Client
Prompt Specification

Version: 1.0


# 1. Purpose

This document defines all prompt templates used by the RPG Chat Client.

All prompts must be centralized and stored in:

src/prompts.py

No prompt text should exist anywhere else in the codebase.


This ensures:

• easy editing
• consistent style
• predictable LLM behavior


# 2. Prompt Design Goals

Prompts are optimized for:

• small models (~3B parameters)
• short context (2048–4096 tokens)
• roleplay stability
• low hallucination risk


Prompts must remain:

short
structured
consistent


# 3. System Prompt

The system prompt defines the behavior of the model.

It must enforce roleplay style and output format.


Example:


You are roleplaying as {character_name}.

Rules:

Write in third person past tense.

Write exactly one paragraph.

Keep responses moderate in length.

Use "quotes" for dialogue.

Use _underscores_ for thoughts.

Use *asterisks* for sounds.

Do not write actions or dialogue for other characters.

Stay in character.

Do not prepend speaker labels like "Character:" or "Player:".


# 4. Context Template

The context block defines the current roleplay state.

It must follow this exact structure.


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

Avoid long paragraphs.

Recommended maximum sizes:

Character Persona: 6 lines
Player Persona: 6 lines
Character Goal: 6 lines
World Scenario: 8 lines
Story Direction: 8 lines
Scene Memory: 10 lines


# 5. Chat Formatting

Chat history must follow this format:


Player: message

Character: message


Example:


Player: Hello, is anyone here?

Character: The guard looks at you suspiciously. "Who are you?"

Internally the system should represent chat as structured message turns.

This allows the ContextBuilder to convert them into role-based messages for the LLM API.


# 6. Context Assembly

The final prompt sent to the LLM must follow this order:


System Prompt

Context Block

Recent Chat History

Next Speaker Prefix


Example:


System Prompt


[Context]

Character Persona:
...

Player Persona:
...


Player: Hello

Character:


# 7. Enhance Prompt

Used when the user chooses "Enhance Message".

Purpose:

Rewrite the user's message in richer roleplay style.


Prompt:


Rewrite the following roleplay message to improve atmosphere and description.

Keep the meaning the same.

Write one paragraph.

Original message:
{user_message}


Enhanced version:


# 8. Summary Prompt

Used for manual memory summarization.

Purpose:

Condense older chat messages into short scene memory.


Prompt:


Summarize the following roleplay events.

Write short factual lines.

One line = one event.

Avoid long explanations.


Example output:

Player arrived in abandoned town
Character distrusts Player
Bell rings at midnight


Chat history:
{chat_history}


Summary:


# 9. Response Length Control

Small models often generate overly long responses.

The system prompt must encourage short responses.

Recommended response length:

60–120 words.


# 10. Hallucination Prevention

The prompts must include rules preventing the model from controlling other characters.

Example rule:


Do not write actions or dialogue for Player.


This prevents the model from breaking roleplay boundaries.


# 11. Prompt Debug Mode

When Prompt Debug Mode is enabled, the system must log context debug data.

Current implementation logs estimated context token count at debug level.


This helps diagnose roleplay issues.


# 12. Prefix Duplication Guardrail

Small models may sometimes emit a prefixed line such as `Character: ...` even
when the next-speaker cue already provides that role.

Prompt rules should explicitly discourage this, and runtime normalization should
still be applied as a defensive fallback.
