# LLM Code Generation Prompt

Use the documentation in the docs directory to generate the source code for the project.

Follow these instructions strictly.


# Instructions

You are generating a Python desktop application.

Follow the architecture defined in:

docs/architecture.md

Follow implementation details in:

docs/implementation_spec.md

Follow coding rules in:

docs/coding_rules.md

Follow prompt design in:

docs/prompts_spec.md

Follow context logic in:

docs/context_builder_design.md

Follow UI layout in:

docs/ui_layout_spec.md


# Requirements

Language: Python 3.10+

GUI: tkinter

Libraries:

requests
tiktoken (optional)


# Project structure

Generate files inside:

src/


Files required:

main.py
ui.py
chat_controller.py
context_builder.py
token_manager.py
memory_manager.py
llm_client.py
prompts.py
models.py


# Important rules

Do not mix UI and business logic.

Use GameState as the central data model.

All prompts must be defined in prompts.py.

Context must be built only by ContextBuilder.

Token calculations must be handled by TokenManager.

LLM communication must be handled only by LLMClient.

Each file should remain under 500 lines.

Normalize stored chat turn text to avoid duplicated leading speaker labels
(for example `Player: Character: ...` in rendered history).

When implementing tkinter input fields, include explicit clipboard shortcuts
for copy/cut/paste/select-all in editable widgets.


# Output format

Generate full code for each file separately.

Begin with models.py.
