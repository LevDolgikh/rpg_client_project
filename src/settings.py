"""Default application settings."""


class AppSettings:
    COMMON_ROLEPLAY_RULES = """Write in third person past tense.
Write exactly one paragraph.
Keep responses short in length.
Use "quotes" for dialogue.
Use _underscores_ for thoughts.
Use *asterisks* for sounds.
Do not write actions or dialogue for other characters.
Stay in character.
Lead events forward."""

    SYSTEM_PROMPT = """You are roleplaying as {character_name}.
Rules:
{rules}""".format(rules=COMMON_ROLEPLAY_RULES, character_name="{character_name}")

    CONTEXT_TEMPLATE = """[Context]
Character Name:
{character_name}
Character Persona:
{character_description}
World Description:
{world_description}
Answer example: I demand top quality work from my assistants. *She pauses, considering.* Alright, I suppose we can give it a shot. But remember, I expect nothing less than your best effort.
"""

    BASE_CONNECTION_OPTIONS = [
        {
            "name": "LM Studio (Local)",
            "base_url": "http://localhost:1234/v1/",
            "type": "local",
        },
        {
            "name": "Ollama (Local)",
            "base_url": "http://localhost:11434/v1/",
            "type": "local",
        },
        {
            "name": "OpenAI (Cloud)",
            "base_url": "https://api.openai.com/v1/",
            "type": "cloud",
        },
    ]
