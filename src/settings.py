"""This file contains the default settings for the application."""

class DEFAULT_SETTINGS:
    # General settings

    COMMON_ROLEPLAY_RULES = """Write in third person past tense.
    Write exactly one paragraph.
    Keep responses short in length.
    Use "quotes" for dialogue.
    Use _underscores_ for thoughts.
    Use *asterisks* for sounds.
    Do not write actions or dialogue for other characters.
    Stay in character.
    Lead events forward."""

    SYSTEM_PROMPT = f"""You are roleplaying as {{character_name}}.
    Rules:
    {COMMON_ROLEPLAY_RULES}"""
    CONTEXT_TEMPLATE = """[Context]
    Character Persona:
    {character_description}
    World Description:
    {world_description}
    """

    BASE_CONNECTION_OPTIONS = [{"name": "LM Studio (Local)", 
                                "base_url": "http://localhost:1234/v1/",
                                "type": "local"},
                               {"name": "Ollama (Local)", 
                                "base_url": "http://localhost:11434/v1/",
                                "type": "local"} ,
                                {"name": "OpenAI (cloud)", 
                                "base_url": "https://api.openai.com/v1/",
                                "type": "cloud"} 
                                # add more options here as needed or change existing ones
                                ]

