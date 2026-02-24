from datetime import datetime
from litellm.exceptions import AuthenticationError, RateLimitError
from rich.console import Console

from core.llm_chat import get_chat_response, create_user_prompt
from core.session import SessionManager
from core.history import HistoryStorage
from core.logger import Logger
from enums import Role
from ui.chat_ui import ChatUI
from config.model import ModelConfig
from config.config import ConfigManager
from const import TITLE_MAX_LENGTH

class ChatApp:
    """ Chat application class for managing the chat UI.
    Attributes:
        session_manager (SessionManager): Manager for conversation sessions.
        history_storage (HistoryStorage): Storage for conversation history.
        console (Console): Rich console for output.
        logger (logging.Logger): Logger for application events and errors.
        ui (ChatUI): User interface for chat interactions.
        model_config (ModelConfig): Configuration for available models.
        main_config (ConfigManager): Main configuration manager for app settings.
    """
    def __init__(self):
        self.logger = Logger().logger
        self.session_manager = SessionManager()
        self.history_storage = HistoryStorage(self.logger)

        self.ui = ChatUI()

        self.model_config = ModelConfig()
        self.main_config = ConfigManager(self.logger, self.ui)

        # Load available models from configuration
        self.model_config.load_models()

    def main_loop(self) -> bool:
        """ Main chat loop for user interaction.
        Returns:
            bool: True to continue the chat, False to exit.
        """
        # Main chat loop
        try:
            if self.session_manager.current_session is None:
                raise Exception("No active session found.")

            # Prompt user for input
            user_input = self.ui.get_user_prompt()
            user_timestamp = datetime.now()
            self.logger.info("User input received.")

            # Get current session history
            history = self.session_manager.current_session.messages

            # If session's title is empty, set it to the first user input
            if len(history) == 0:
                self.session_manager.current_session.title = user_input[:TITLE_MAX_LENGTH]
                self.logger.info(f"Session title set to: {self.session_manager.current_session.title}")

            with self.ui.waiting_indicator():
                # Get model configuration for current session
                model = self.model_config.get_model(self.session_manager.current_session.model)

                # Check if model configuration is found
                if model is None:
                    raise Exception(f"Model '{self.session_manager.current_session.model}' not found.")

                # Get AI response
                self.logger.info(f"Sending user input to model '{model.model_id}' for response.")
                response = get_chat_response(
                    model=model.model_id,
                    system_prompt=self.main_config.config.system_prompt,
                    user_prompt=create_user_prompt(
                        user_input, 
                        current_time=user_timestamp
                    ),
                    history=history,
                    thinking=model.thinking
                )

            self.ui.print_ai_message(response)
            assistant_timestamp = datetime.now()
            self.logger.info("AI response received and displayed to user.")

            # Append user message and AI response to session
            self.session_manager.current_session.append_message(
                role=Role.USER,
                content=user_input,
                timestamp=user_timestamp
            )
            self.session_manager.current_session.append_message(
                role=Role.ASSISTANT,
                content=response,
                timestamp=assistant_timestamp
            )
            self.logger.info("User input and AI response added to session history.")

            return True

        except (KeyboardInterrupt, EOFError):
            # Exit on Ctrl+C or Ctrl+D
            return False

        except AuthenticationError:
            self.ui.print_error("Invalid API key or credentials.")
            self.logger.error("Error during sending request to model: Authentication failed.")
            return False

        except RateLimitError:
            self.ui.print_message("Rate limit exceeded. Please try again later.")
            self.logger.error("Error during sending request to model: Rate limit exceeded.")
            return True

        except Exception as e:
            self.ui.print_error(f"Unexpected error occurred. Please check the logs for more details.")
            self.logger.error(f"Unexpected error during main loop: {str(e)}", stack_info=True)
            return False

    def start_chat(self):
        """ Start an interactive chat session with the AI assistant.
        """
        self.logger.info("Starting chat application.")

        try: 
            # Let user select a session from history
            choice = self.ui.select_session(self.history_storage.histories)
        except (KeyboardInterrupt, EOFError):
            # Exit on Ctrl+C or Ctrl+D
            self.ui.print_exit_message()
            return

        # Load selected session
        if choice is not None:
            # Get history data
            filename = self.history_storage.histories[choice].filename
            history_data = self.history_storage.get_history(filename)

            # Load session into session manager
            self.session_manager.load_session(history_data)

            # Print existing conversation history
            self.ui.print_session_history(self.session_manager.current_session.messages)
        else:
            # Create a new session if none selected
            default_model = self.main_config.config.default_model
            self.session_manager.create_session(default_model)

        continue_chat = True
        while continue_chat:
            continue_chat = self.main_loop()

        # Save conversation history on exit
        session_data = self.session_manager.current_session
        if session_data is not None:
            self.history_storage.save_history(session_data)
            self.logger.info("Chat session ended and history saved.")

        self.ui.print_exit_message()

if __name__ == "__main__":
    chat_app = ChatApp()
    chat_app.start_chat()
