from google import genai
from google.genai import types
from google.genai.types import GenerateContentResponse
from google.genai.errors import ClientError

class GoogleAIChat:
    def __init__(self):
        self.client = genai.Client(api_key="API_KEY")
        self.model = "gemini-flash-latest"
        self.system_prompt = "You are a helpful assistant."
        self.chat = None

    def create_chat(self, history):
        self.chat = self.client.chats.create(
            model=self.model,
            history=history,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0,
                )
            )
        )

    def generate_response(self, user_input: str) -> str:
        if self.chat is None:
            self.create_chat([])

        try:
            response: GenerateContentResponse = self.chat.send_message(user_input)
        except ClientError as e:
            return f"Error: {e.message}"

        return response.text


