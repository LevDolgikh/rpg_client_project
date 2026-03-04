# RPG Chat Client
System Architecture

Version: 1.0


# 1. Overview

This document describes the internal architecture of the RPG Chat Client.

The architecture is designed to:

• keep code modular and readable  
• allow easy LLM-assisted code generation  
• minimize coupling between UI and logic  
• support small-model context optimization


The system is divided into several core modules.


# 2. Core Modules

The application consists of the following modules:

UI  
ChatController  
ContextBuilder  
TokenManager  
MemoryManager  
LLMClient  


Each module has a clearly defined responsibility.


# 3. Data Model

All game data is stored in a single object:

GameState


GameState contains the entire session state and is used by all modules.


# 4. GameState Structure

GameState fields:

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


chat_history is stored as a list of chat messages.


Example:

[
 ("Player", "Hello"),
 ("Character", "The guard eyes you suspiciously.")
]


GameState must be serializable to JSON.


# 5. UI Module

Responsibilities:

• render the graphical interface  
• display current GameState  
• collect user input  
• send actions to ChatController  


The UI must not contain business logic.


UI only interacts with ChatController.


# 6. ChatController

ChatController coordinates the system.

Responsibilities:

• update GameState  
• handle user actions  
• call ContextBuilder  
• call LLMClient  
• update chat history  


Example flow:

User clicks "Generate Response"  
→ ChatController builds prompt  
→ ChatController calls LLMClient  
→ response is added to GameState.chat_history  
→ UI updates display


# 7. ContextBuilder

ContextBuilder constructs prompts for the LLM.

Responsibilities:

• assemble context block  
• insert system prompt  
• include scene memory  
• include recent chat history  
• apply token trimming when necessary


Output:

messages list compatible with OpenAI API format.


Example:

[
 {"role":"system","content": "..."},
 {"role":"user","content": "..."}
]


# 8. Context Structure

Each LLM request follows this structure:


System Prompt


[Context]

Character Persona

Player Persona

Character Goal

World Scenario

Story Direction

Scene Memory


Recent Chat History


User Input


The structure must remain consistent across all requests.


# 9. TokenManager

TokenManager monitors token usage.

Responsibilities:

• estimate token usage  
• track context size  
• enforce memory limit  
• assist ContextBuilder during trimming


TokenManager must support two modes:

tiktoken installed  
fallback estimator


Fallback estimation rule:

1 token ≈ 4 characters


# 10. History Trimming

If the context exceeds the memory limit:

ContextBuilder removes the oldest chat messages.

Priority order for preservation:

System prompt  
Context fields  
Scene memory  
Recent chat history  


Recent messages always have priority.


# 11. MemoryManager

MemoryManager manages scene memory.

Responsibilities:

• summarize older chat  
• update scene_memory field


The system does NOT run automatic summarization.

The user triggers summarization manually using "Make Summary".


Summary flow:

User clicks "Make Summary"  
→ selected chat messages are sent to LLM  
→ LLM returns condensed summary  
→ summary replaces part of chat history


# 12. LLMClient

LLMClient communicates with LM Studio.

Protocol:

OpenAI compatible API.


Endpoint:

POST /v1/chat/completions


Responsibilities:

• send requests to LLM  
• stream responses  
• allow generation cancellation  
• return generated text


LLMClient does not know anything about GameState.


It only processes prompts.


# 13. Save / Load System

Save and load operations serialize GameState.

File format:

JSON


Example structure:

{
 "player_name": "...",
 "character_name": "...",
 "player_description": "...",
 "character_description": "...",
 "character_goal": "...",
 "world_scenario": "...",
 "story_direction": "...",
 "scene_memory": "...",
 "chat_history": [...]
}


# 14. Data Flow

Typical generation flow:


User input

↓

UI

↓

ChatController

↓

ContextBuilder

↓

TokenManager

↓

LLMClient

↓

ChatController

↓

GameState update

↓

UI refresh


This flow must remain consistent.


# 15. Chat Text Normalization

To maintain a stable internal turn format, ChatController normalizes turn text
before appending to `GameState.chat_history`.

Normalization removes leading speaker labels from message text (for example
`Player:` or `Character:`) when they are redundantly included in model output.

GameState load parsing applies the same normalization for compatibility with
older save files.
