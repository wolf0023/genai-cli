from litellm import acompletion, ModelResponse, CustomStreamWrapper, Choices, StreamingChoices
from datetime import datetime

from genai_cli.enums import Role
from genai_cli.core.session import Message

class LLMChat:
    """ A class to handle interactions with the LLM model for chat-based conversations. 

    Attributes:
        logger: A logging instance to log messages and errors.
    """

    def __init__(self, logger):
        """ Initialize the LLMChat instance.

        Args:
            logger: A logging instance to log messages and errors.
        """
        self.logger = logger

    def create_user_prompt(
        self,
        user_prompt: str, 
        current_time: datetime | None = None
    ) -> str:
        """ Create an user prompt for the LLM model.
        Args:
            user_prompt: The user's prompt.
            current_time: The current timestamp.
        Returns:
            The formatted user prompt as a string.
        """
        # If current_time is not provided, use the current timestamp
        if current_time is None:
            current_time = datetime.now()

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

    def get_sendable_format(
        self,
        message: Message
    ) -> dict[str, str]:
        """ Convert a Message object to a sendable format for the LLM model.
            Args:
                message: The Message object to convert.
            Returns:
                A dictionary with 'role' and 'content' keys.
        """
        return {
            "role": message.role.value,
            "content": message.content
        }

    async def get_chat_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        history: list[Message],
        thinking: bool = False
    ) -> str:
        """ Get a chat response from the LLM model.
            Args:
                model: The LLM model to use.
                system_prompt: The system prompt to set the context.
                user_prompt: The user's prompt.
                history: The conversation history as a list of Message objects.
                thinking: Whether to use thinking mode (if applicable).
            Returns:
                The LLM's response as a string.
        """
        messages: list[dict[str, str]] = [self.get_sendable_format(msg) for msg in history]

        # Add the system prompt to the messages if provided
        if system_prompt:
            messages.insert(0, {"role": Role.SYSTEM.value, "content": system_prompt})

        # Add the user's prompt to the messages
        messages.append({"role": Role.USER.value, "content": user_prompt})

        # Get the completion from the LLM model
        response: ModelResponse|CustomStreamWrapper = await acompletion(
            model=model, 
            messages=messages,
            reasoning_effort="medium" if thinking else None
        )

        # Avoid 'Attribute "choices" is unknown'
        assert isinstance(response, ModelResponse)

        # Log token usage information if available
        if hasattr(response, "usage") and response.usage is not None:
            self.logger.info(f"Prompt tokens: {response.usage.get('prompt_tokens', 'N/A')}")
            self.logger.info(f"Completion tokens: {response.usage.get('completion_tokens', 'N/A')}")

        # Get the first choice from the response
        choice: Choices|StreamingChoices = response.choices[0]

        # Avoid 'Attribute "message" is unknown'
        assert isinstance(choice, Choices)

        return choice.message["content"]

