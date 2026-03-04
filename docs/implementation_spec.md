# RPG Chat Client
Implementation Specification

Version: 1.0


# 1. Overview

This document defines the concrete implementation structure of the application.

It specifies:

• file structure  
• classes  
• responsibilities  
• key methods  


The goal is to ensure predictable code generation when using LLM.


# 2. Project Structure

Source code must follow this structure:


src/

main.py

ui.py

chat_controller.py

context_builder.py

token_manager.py

memory_manager.py

llm_client.py

prompts.py

models.py


Each file should remain under ~500 lines when possible.


# 3. models.py

Defines data models.

Primary model:

GameState


GameState fields:

player_name : str  
character_name : str  

player_description : str  
character_description : str  

character_goal : str  

world_scenario : str  

story_direction : str  

scene_memory : str  

chat_history : list  

settings : dict  


chat_history format:

[
 ("Player", "Hello"),
 ("Character", "The guard watches you carefully.")
]


GameState must support:

to_dict()

from_dict()

for JSON serialization.


# 4. main.py

Application entry point.

Responsibilities:

• initialize UI  
• create GameState  
• initialize controller modules  


Typical structure:

create GameState

create ChatController

launch UI


# 5. ui.py

Implements the graphical interface using tkinter.

Responsibilities:

• render interface components  
• display chat history  
• display token usage  
• collect user input  
• send actions to ChatController  


UI must not contain business logic.


UI communicates only with ChatController.


# 6. chat_controller.py

Central coordination module.

Class:

ChatController


Responsibilities:

• update GameState  
• process user actions  
• generate responses  
• enhance messages  
• manage history  


Main methods:


send_message()

generate_response()

enhance_message()

redo_response()

make_summary()

delete_last_message()


ChatController must call:

ContextBuilder

LLMClient

MemoryManager


Bug fix note:

Chat history in UI is read-only to preserve internal turn structure and keep
redo_response() deterministic.

To support user correction, deletion is handled through ChatController.delete_last_message().


# 7. context_builder.py

Class:

ContextBuilder


Responsibilities:

• assemble prompt messages  
• insert context fields  
• attach scene memory  
• attach chat history  
• apply token trimming


Main methods:


build_messages()

build_context_block()

build_chat_history()

trim_history()


Output must follow OpenAI messages format.


# 8. token_manager.py

Class:

TokenManager


Responsibilities:

• estimate token usage  
• check context limits  
• assist history trimming  


Main methods:


count_tokens()

estimate_tokens()

check_limit()


Supports two modes:

tiktoken available

fallback estimator


Fallback rule:

1 token ≈ 4 characters


# 9. memory_manager.py

Class:

MemoryManager


Responsibilities:

• summarize chat history  
• update scene memory  


Main method:


create_summary()


Workflow:

old chat → LLM → summary → scene_memory


# 10. llm_client.py

Class:

LLMClient


Responsibilities:

• communicate with LM Studio  
• send requests  
• receive responses  
• support streaming  


Endpoint:

POST /v1/chat/completions


Main methods:


generate()

generate_stream()


The client must remain independent of GameState.


# 11. prompts.py

Contains all prompt templates.

No prompts should exist outside this file.


Defined prompts:

SYSTEM_PROMPT

CONTEXT_TEMPLATE

SUMMARY_PROMPT

ENHANCE_PROMPT


These templates are used by ContextBuilder.


# 12. Save / Load

Game state must be saved as JSON.

Workflow:

GameState → dict → JSON file


Load workflow:

JSON file → dict → GameState


# 13. Streaming Response Handling

Streaming generation should append tokens to the chat window progressively.

User must be able to cancel generation.


# 14. Error Handling

The system must handle:

connection errors

server unavailable

timeout

invalid responses


Errors should be reported through UI messages.


# 15. Message Text Normalization

To prevent duplicated speaker labels in chat history:

- `ChatController.send_message()` must normalize text before storing.
- `ChatController.generate_response()` must normalize model output before storing.
- `GameState.from_dict()` must normalize loaded history for backward compatibility.

Normalization rule:

If message text starts with a known speaker label plus colon (for example
`Player:` or `Character:`), strip the leading label from message text and keep
speaker identity in the tuple field.


# 16. Clipboard Bindings in UI

`ui.py` must provide explicit clipboard shortcuts for editable widgets (`Text`,
`Entry`, `TEntry`) to ensure reliable behavior across environments.

Required shortcuts:

- `Ctrl+C` / `Ctrl+Insert` => copy
- `Ctrl+X` / `Shift+Delete` => cut
- `Ctrl+V` / `Shift+Insert` => paste
- `Ctrl+A` => select all
