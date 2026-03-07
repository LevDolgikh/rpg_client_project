COMMON_ROLEPLAY_RULES = """Write in third person past tense.

Write exactly one paragraph.

Keep responses short in length.

Use "quotes" for dialogue.

Use _underscores_ for thoughts.

Use *asterisks* for sounds.

Do not write actions or dialogue for other characters.

Stay in character.

Lead events forward.

Do not prepend speaker labels like "Character:" or "Player:"."""


SYSTEM_PROMPT = f"""You are roleplaying as {{character_name}}.

Rules:

{COMMON_ROLEPLAY_RULES}"""


CONTEXT_TEMPLATE = """[Context]

Character Persona:
{character_description}

Player Persona:
{player_description}

Story Intent:
{story_intent}

World Description:
{world_scenario}

Scene Memory:
{scene_memory}"""


SUMMARY_PROMPT = """Summarize the following roleplay events.

Write short factual lines.

One line = one event.

Avoid long explanations.

Use only facts from Chat history.

Do not copy templates or examples.

Do not add headings, introductions, or closing lines.

Chat history:
{chat_history}


Summary (lines only):"""
