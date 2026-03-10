"""
Game client module for managing game state and interactions with the LLM client.
Steps of development:
1. Basic game (current step)
2. Stream support
3. Token cut support
4. Additional settings support (temperature, max tokens, etc.)
5. Summary support
"""

import settings
from llm_client import LLMClient

class RPG_client:
    """Main class for the RPG client application, responsible for managing game state and interactions with the LLM client"""
    
    def __init__(self):
        """Initialize the RPG client with a reference to the LLM client and default game state"""
        self.llm_client = LLMClient()

    def connect_to_llm(self, base_url, api_key):
        """Connect to the LLM server using the provided base URL and API key, returns True if successful, False otherwise"""
        return self.llm_client.connect(base_url, api_key)
    
    def disconnect_from_llm(self):        
        """Disconnect from the LLM server and reset client state"""
        self.llm_client.disconnect()
    
    def get_available_models(self):
        """Get a list of available models from the LLM server, returns a list of model IDs"""
        return self.llm_client.get_model_ids()
    
    def set_active_model(self, model_id):
        """Set the active model for generating responses, returns True if successful, False if model_id is not in the list of available models"""
        return self.llm_client.set_model(model_id)
    
    def generate_responce(self, 
                          character_name,
                          character_description,
                          world_description,
                          message_history):
        """Generate a response from the LLM based on the current game state and player input, returns the generated response text"""

        # Format the system prompt with the current game state
        system_prompt = settings.DEFAULT_SETTINGS.CONTEXT_TEMPLATE.format(
            character_name=character_name,
            character_description=character_description,
            world_description=world_description,
        )

        response = self.llm_client.generate_response(system_prompt, message_history)
        return response

if main := __name__ == "__main__":
    """Test the RPG client by connecting to a local LLM server, setting up a sample game state, and generating a response based on a sample message history"""
    
    # System message formating test
    character_name = "Greg"
    character_description = "A funny guy"
    world_description = "Modern world"
    story_intent = "Greg talk with random person" 

    base_url = "http://127.0.0.1:1234/v1" # Local LM Studio
    #base_url = "http://localhost:11434/v1/" # Ollama

    rpg_client = RPG_client()
    message = "hi! what is your name?"

    rpg_client.connect_to_llm(base_url=base_url, api_key="")
    response = rpg_client.generate_responce(character_name, 
                                 character_description, 
                                 world_description,
                                 story_intent, 
                                 message)
    print("Generated response:", response)
    