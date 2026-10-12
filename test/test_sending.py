import logging
import asyncio
import litellm
from genai_cli.core.llm_chat import LLMChat
from genai_cli.config.model import ThinkingLevel

def test_send_message():
    litellm.suppress_debug_info = True

    logger = logging.getLogger("test_sending_logger")
    logger.setLevel(logging.DEBUG)
    llm_chat = LLMChat(logger)

    user_input = "hello"
    system_prompt = "Please response in two sentences."

    response = asyncio.run(llm_chat.get_chat_response(
        model="azure/gpt-6-luna",
        system_prompt=system_prompt,
        user_prompt=llm_chat.create_user_prompt(
            user_prompt=user_input,
            current_time=None
        ),
        history=[],
        thinking=ThinkingLevel.MEDIUM
    ))

    print(f"{user_input} -> {response}")
    assert True
