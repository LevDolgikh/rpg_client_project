"""
Client for interacting with OpenAI Compatible server to generate responses based on system instructions and user prompts
Steps of development:
1. Basic instructions. (current step)
2. Stream support
3. Additional settings support (temperature, max tokens, etc.)
"""

from openai import OpenAI

class LLMClient:
    """Client for interacting with OpenAI Compatible server to generate responses based on system instructions and user prompts"""
    
    def __init__(self):
        """Initialize the LLM client with the base URL and API key for the LLM server"""
        self.client = ""
        self.current_model = ""
        self.models = ""
        self.model_ids = ""
        self.status = "Disconnected"
        
    def connect(self, base_url, api_key):
        """Connect to the LLM server with the provided base URL and API key, 
        returns model list if successful. Example [chatGPT-40, llama 2b,...]"""
        try:
            self.client = OpenAI(base_url=base_url, 
                                 api_key=api_key)
            self.models = self.get_models()
        except:
            self.status = "Disconnected"
            return ""
        
        if self.models:
            self.current_model = self.models[0].id

        self.status = "Connected"

        model_list = []
        for model in self.models:
            model_list.append(model.id)
  
        self.model_ids = model_list

        return model_list
    
    def disconnect(self):        
        """Reset client state"""
        if self.client:
            self.client.close()
            self.client = ""
        self.current_model = ""
        self.models = ""
        self.model_ids = ""
        self.status = "Disconnected"

    def get_models(self):
        """Get a list of available models from the LLM server"""
        try:
            return self.client.models.list().data
        except:
            return ""
        
    def get_model_ids(self):
        if self.status == "Connected":
            return  self.model_ids
        else:
            return ""
    
    def set_model(self, model_id):
        """Set model by id, returns True if successful, False if model_id is not in the list of available models"""
        if model_id in self.model_ids:
            self.current_model = model_id
            return True
        else:
            return False

    def generate_response(self, instructions, input):
        """Generate a response from the LLM based on the system instructions and user prompt history"""
        try:
            response = self.client.responses.create(
                model=self.current_model,
                instructions=instructions,
                input=input,
                stream = False,
            )
            return response.output_text
        except:
            return ""
        
    def generate_response_stream(self, instructions, input):
        """Generate a response from the LLM based on the system instructions and user prompt history"""
        try:
            response = self.client.responses.create(
                model=self.current_model,
                instructions=instructions,
                input=input,
                stream = True,
            )
            return response
        except:
            return ""
    
if main := __name__ == "__main__":
        """Test the LLM client by connecting to the local server, retrieving available models, and generating a response based on a sample message history"""
        base_url = "http://127.0.0.1:1234/v1" # LM Studio
        # base_url = "http://localhost:11434/v1/" # Ollama
        
        client = LLMClient()

        if client.connect(base_url=base_url, api_key=""):
            print("Connected to LLM server")
            print("Available models:", client.get_models())
            print("Current model:", client.current_model)
        else:
            print("Failed to connect to LLM server")
        
        instructions = "You are Greg, a funny guy"
        message = "what is your name?"

        # Static response
        response = client.generate_response(instructions, message)
        print("LLM Response:", response)
        
        # Streaming response
        response_stream = client.generate_response_stream(instructions, message)
        print("Streaming response: ")
        for event in response_stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="")   # печатаем фрагмент текста без перевода строки
            elif event.type == "response.completed":
                print("\n[Ответ завершён]")
