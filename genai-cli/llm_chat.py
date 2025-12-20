from litellm import completion, ModelResponse, CustomStreamWrapper, Choices, StreamingChoices
from datetime import datetime
import dotenv

from enums import Role

dotenv.load_dotenv()

def create_user_prompt(
    user_prompt: str, 
    current_time: datetime = datetime.now()
) -> str:
    """ Create an user prompt for the LLM model.
    Args:
        user_prompt: The user's prompt.
        current_time: The current timestamp.
    Returns:
        The formatted user prompt as a string.
    """
    time_str: str = current_time.isoformat(sep=' ', timespec='seconds')
    time_zone: str = current_time.astimezone().tzname() or "UTC"

    return f"""
    <current_time>
        {time_str} ({time_zone})
    </current_time>
    <user_prompt>
        {user_prompt.strip()}
    </user_prompt>
    """.strip()

def get_chat_response(
    model: str,
    system_prompt: str,
    user_prompt: str,
    history: list[dict[str, str]],
):
    """ Get a chat response from the LLM model.
        Args:
            model: The LLM model to use.
            system_prompt: The system prompt to set the context.
            user_prompt: The user's prompt.
            history: The chat history as a list of messages.
        Returns:
            The LLM's response as a string.
    """
    messages: list[dict[str, str]] = []

    # Add the system prompt to the messages if provided
    if system_prompt:
        messages.append({"role": Role.SYSTEM.value, "content": system_prompt})

    # Add the chat history to the messages
    messages.extend(history)

    # Add the user's prompt to the messages
    messages.append({"role": Role.USER.value, "content": user_prompt})

    # Get the completion from the LLM model
    response: ModelResponse|CustomStreamWrapper = completion(
        model=model, 
        messages=messages,
    )

    # Avoid 'Attribute "choices" is unknown'
    if isinstance(response, CustomStreamWrapper):
        return "Something went wrong. Please try again."

    choice: Choices|StreamingChoices = response.choices[0]

    # Avoice 'Attribute "message" is unknown'
    if isinstance(choice, StreamingChoices):
        return "Something went wrong. Please try again."

    return choice.message["content"]

