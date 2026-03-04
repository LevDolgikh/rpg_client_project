# RPG Chat Client
Product Specification

Version: 1.0


# 1. Purpose

The application is a desktop client designed for role-playing chat with local LLM models using LM Studio.

The system is optimized for:

- small local models (~3B parameters)
- limited context length (2048–4096 tokens)

The program must allow the user to control story development while interacting with the language model.


# 2. Key Goals

The program must provide:

• strong control over story direction  
• transparent token usage  
• efficient context management  
• manual control over memory and summaries  

The system must avoid hidden automated behavior.


# 3. Target Environment

Local machine.

Typical configuration:

LLM size: ~3B parameters  
Context length: 2048–4096 tokens  
Backend: LM Studio local server


# 4. Core Concept

The application allows a user to roleplay with an AI character.

Two characters exist in the system:

Player  
Character

The user can:

• write messages for Player  
• write messages for Character  
• generate responses for Player  
• generate responses for Character  
• enhance messages using the LLM


# 5. Main UI Sections

The interface contains the following areas:

Server Status

Character Setup

Descriptions

Character Goal

World Scenario

Story Direction

Scene Memory

Chat History

Message Input

Token Monitor

Controls

Advanced Options


# 6. Character Setup

Fields:

Player Name  
Character Name


# 7. Description Fields

Player Description

Short description of the player's character.

Character Description

Description of the AI character including personality and behavior.

Character Goal

Short statements describing the character's motivations or hidden intentions.

World Scenario

Description of the current setting and situation.

Story Direction

Instructions guiding story development.

Scene Memory

Short summary of important past events.


# 8. Writing Rules for Context Fields

All context fields should follow this format:

One line = one idea.

Example:

Character distrusts Player  
Town feels abandoned  
Church bell rings at night

Avoid long paragraphs.

## Context Size Recommendations

To ensure stable operation with small local models (3B parameters)
and limited context (2048–4096 tokens), the following limits are recommended.

World Scenario:
maximum 6–8 lines

Story Direction:
maximum 6–8 lines

Character Goal:
maximum 4–6 lines

Scene Memory:
maximum 10 lines

Each line should contain a short factual statement.

Avoid long paragraphs.

Example:

Character distrusts Player
Town feels abandoned
Bell rings at night


# 9. Chat System

Chat history follows this format:

Player: message  
Character: message


# 10. Message Actions

Send Message

Adds a message to the chat.

Generate Response

The LLM generates a response for the selected speaker.

Enhance Message

The LLM rewrites the message to improve roleplay style.

Redo Response

Generates an alternative version of the last response.


# 11. Token Monitoring

The interface must display:

Current context token usage  
Maximum token limit  
Estimated tokens in the last generated output

Color indicators:

Green — below 60%  
Orange — 60–80%  
Red — above 80%


# 12. Memory System

The program uses manual memory management.

A button called "Make Summary" allows the user to summarize older chat messages.

The summary is stored in Scene Memory.


# 13. Context Structure

Each LLM request is built from:

System Prompt

Context Block:
Character Persona
Player Persona
Character Goal
World Scenario
Story Direction
Scene Memory

Recent Chat History

User Input


# 14. Advanced Options

Advanced options include:

Temperature  
Top P  
Presence Penalty  
Frequency Penalty  
Max Tokens  

Prompt Debug Mode


# 15. Save / Load System

The program must allow saving and loading game state.

Saved data includes:

character names  
descriptions  
character goal  
world scenario  
story direction  
scene memory  
chat history  
settings


# 16. Message Normalization Rules

To keep chat history clean and consistent:

- Stored message text must not include duplicated speaker prefixes.
- If generated text starts with `Player:` or `Character:`, the prefix should be removed before storing.
- The same normalization should run when loading saved chat history.

This prevents artifacts such as:

`Player: Character: ...`


# 17. Input Editing Usability

Editable text fields should support standard clipboard shortcuts:

- Copy: `Ctrl+C` and `Ctrl+Insert`
- Cut: `Ctrl+X` and `Shift+Delete`
- Paste: `Ctrl+V` and `Shift+Insert`
- Select all: `Ctrl+A`

