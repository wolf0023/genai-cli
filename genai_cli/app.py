from datetime import datetime
from litellm.exceptions import AuthenticationError, RateLimitError, BadRequestError
import dotenv
from jsonschema import ValidationError

from genai_cli.core.session import SessionManager
from genai_cli.core.history import HistoryStorage
from genai_cli.core.logger import Logger
from genai_cli.core.llm_chat import LLMChat
from genai_cli.enums import Role
from genai_cli.ui.chat_ui import ChatUI
from genai_cli.config.model import ModelConfig
from genai_cli.config.config import ConfigManager
from genai_cli.command.handler import CommandHandler
from genai_cli.command.registry import CommandRegistry
from genai_cli.command.completion import CommandCompleter
from genai_cli.command.help_command import HelpCommand
from genai_cli.command.sessions_command import SessionsCommand
from genai_cli.command.new_command import NewCommand
from genai_cli.command.select_command import SelectCommand
from genai_cli.command.exit_command import ExitCommand
from genai_cli.command.models_command import ModelsCommand
from genai_cli.command.model_command import ModelCommand
from genai_cli.command.base import CommandError, ExitError
from genai_cli.const import TITLE_MAX_LENGTH
from genai_cli.const import DEFAULT_SESSION_TITLE

class ChatApp:
    """ Chat application class for managing the chat UI.
    Attributes:
        session_manager (SessionManager): Manager for conversation sessions.
        history_storage (HistoryStorage): Storage for conversation history.
        command_registry (CommandRegistry): Registry for available commands in the application.
        command_handler (CommandHandler): Handler for executing commands based on user input.
        command_completer (CommandCompleter): Completer for command auto-completion in the chat UI.
        console (Console): Rich console for output.
        logger (logging.Logger): Logger for application events and errors.
        ui (ChatUI): User interface for chat interactions.
        model_config (ModelConfig): Configuration for available models.
        main_config (ConfigManager): Main configuration manager for app settings.
        is_input_blocked (bool): A flag to indicate whether user input is currently blocked (e.g., while processing a command or waiting for an LLM response).
    """
    def __init__(self):
        self.logger = Logger().logger
        self.session_manager = SessionManager()
        self.history_storage = HistoryStorage(self.logger)

        self.model_config = ModelConfig()
        self.main_config = ConfigManager(self.logger)

        self.command_registry = CommandRegistry(self.logger)
        self.command_handler = CommandHandler(self.logger, self.command_registry)
        self.command_completer = CommandCompleter(self.logger, self.command_registry)

        # Initialize command completions for the chat UI based on the commands available in the CommandHandler.
        self.ui = ChatUI(
            self.command_completer,
            self.handle_user_input
        )

        self.llm_chat = LLMChat(self.logger)

        # Load configurations for models and main settings.
        self._load_configurations()

        # Register all available commands in the command registry.
        self._register_all_commands()

        # A flag to indicate whether user input is currently blocked (e.g., while processing a command or waiting for an LLM response).
        self.is_input_blocked: bool = False

    def _load_configurations(self):
        """ Load model and main configurations.

        Raises:
            ValueError: If there is an error in loading model configuration, a ValueError will be raised with a message prompting the user to check the model configuration file.

            ValidationError: If there is an error in loading main configuration, a ValidationError will be raised with a message indicating that the default configuration will be loaded instead.

            Exception: If there is any unexpected error during loading configurations, a generic Exception will be raised with a message indicating that an unexpected error occurred, and the error details will be logged for further investigation.
        """
        # Load model configuration and main configuration.
        try:
            self.model_config.load_models()
            self.main_config.load_config()

        except ValueError:
            self.logger.error(f"Error in loading model configuration: Please check your model configuration file.")
            raise # Re-raise the exception to prevent starting the app without model configuration

        except ValidationError:
            self.ui.print_error(f"Error in loading configuration: Loading default configuration instead.")

        except Exception as e:
            self.ui.print_error(f"Unexpected error in loading configurations.")
            self.logger.error(f"Unexpected error in loading configurations: {str(e)}", exc_info=True)
            raise # Re-raise the exception to prevent starting the app without proper configuration

    def _register_all_commands(self):
        commands_to_register = [
            HelpCommand(
                get_main_commands_callback=lambda: self.command_registry.commands
            ),
            SessionsCommand(
                get_current_session_callback=lambda: self.session_manager.current_session,
                get_histories_callback=lambda: self.history_storage.histories
            ),
            SelectCommand(
                get_histories_callback=lambda: self.history_storage.histories,
                get_history_callback=self.history_storage.get_history,
                load_session_callback=self.session_manager.load_session,
                get_current_session_callback=self.session_manager.get_current_session
            ),
            NewCommand(
                main_config=self.main_config.config,
                create_new_session_callback=self.session_manager.create_session
            ),
            ModelsCommand(
                models=self.model_config.models
            ),
            ModelCommand(
                models=self.model_config.models,
                get_current_model_callback=
                    lambda: self.session_manager.current_session.model
                    if self.session_manager.current_session is not None else None,
                change_model_callback=self.session_manager.change_model
            ),
            ExitCommand(),
        ]

        for command in commands_to_register:
            try:
                self.command_registry.register(command)
                self.logger.info(f"Registered command: {command.name}")
            except ValueError as e:
                self.logger.error(f"Failed to register command: {e}")

    def _create_status_message(
        self,
        model_name: str | None = None,
        session_title: str | None = None,
    ) -> str:
        """Create a status message for the status filed that includes the current model name and session title if provided.

        Args:
            model_name (str | None): The name of the current model being used in the conversation.
            session_title (str | None): The title of the current conversation session.
        """
        info_parts: list[str] = []
        if model_name:
            info_parts.append(f"[Model] {model_name}")
        if session_title:
            info_parts.append(f"[Session] {session_title}")

        return "  ".join(info_parts)

    def _update_status_and_info(
        self,
        additional_info: str = ""
    ):
        """Update the status bar and information section in the chat UI based on the current sesison's model and title, along with any additional information provided.

        Args:
            additional_info (str): Any additional information to be displayed in the information section of the chat UI, such as error messages, tips, or other relevant details that the user should be aware of.
        """

        if self.session_manager.current_session is not None:
            self.ui.update_status_bar(
                self._create_status_message(
                    model_name=self.session_manager.current_session.model,
                    session_title=self.session_manager.current_session.title,
            ))
            self.ui.update_info(additional_info)
        else:
            self.ui.update_status_bar("No active session")
            self.ui.update_info(additional_info)

    async def _process_command(self, user_input: str) -> bool:
        """ Process a user input that is identified as a command.

        Args:
            user_input (str): The raw user input string that represents a command.

        Returns:
            bool: A boolean value indicating whether the application should continue running (True) or exit (False) after processing the command.
        """
        try:
            self.logger.info(f"Processing command: {user_input}")
            argc, argv = self.command_handler.parse_command(user_input)

            previous_session = self.session_manager.current_session
            output = self.command_handler.handle_command(argc, argv)

            # Print the result of the command execution to the user interface.
            self.ui.print_command_output(user_input, output)

            # Check if the current session has changed after executing the command (e.g., a new session was created or an existing session was loaded).
            if self.session_manager.current_session is not previous_session:
                # If there was a previous session before executing the command, save its history to the history storage.
                if previous_session is not None:
                    self.history_storage.save_history(previous_session)
                    self.logger.info(f"Previous session '{previous_session.title}' saved to history.")

                # If the session has changed, update the chat history display in the user interface to reflect the messages of the new current session.
                self.logger.info("Session changed after command execution. Updating chat history display.")
                new_history = self.session_manager.current_session.messages
                self.ui.print_histories(new_history)

            return True

        except CommandError as e:
            self.ui.print_error(str(e))
            return True

        except ExitError:
            return False

        except Exception as e:
            self.ui.print_error(f"Unexpected error occurred. Please check the logs for more details.")
            self.logger.error(f"Unexpected error during handling command: {str(e)}", exc_info=True)
            return False

    async def _process_llm_response(self, user_input: str) -> bool:
        """Process a user input that is identified as a message to the LLM, sending the input to the model and handling the response.

        Args:
            user_input (str): The raw user input string that is intended to be sent to the LLM model for a response.

        Returns:
            bool: A boolean value indicating whether the application should continue running (True) or exit (False) after processing the LLM response.
        """
        try:
            # Record the timestamp of the user input to associate it with the corresponding AI response in the session history.
            user_timestamp = datetime.now()
            self.logger.info("Processing user input for LLM response.")

            # Check if there is an active session before processing the LLM response.
            if self.session_manager.current_session is None:
                self.logger.error("No active session found when processing LLM response.")
                raise Exception("No active session found. Please create or load a session before sending messages.")

            # Get current session history
            history = self.session_manager.current_session.messages

            # If session's title is empty, set it to the first user input
            if len(history) == 0 and self.session_manager.current_session.title == DEFAULT_SESSION_TITLE:
                self.session_manager.current_session.title = ''.join(user_input.split())[:TITLE_MAX_LENGTH]
                self.logger.info(f"Session title set to: {self.session_manager.current_session.title}")

            # Get model configuration for current session
            model = self.model_config.get_model(self.session_manager.current_session.model)

            # Check if model configuration is found
            if model is None:
                raise Exception(f"Model '{self.session_manager.current_session.model}' not found.")

            # Append user input to chat UI before sending request to model, so that user can see their message immediately.
            self.ui.print_conversation(user_input, role=Role.USER)

            # Get AI response
            self.logger.info(f"Sending user input to model '{model.model_id}' for response.")
            response = await self.llm_chat.get_chat_response(
                model=model.model_id,
                system_prompt=self.main_config.config.system_prompt,
                user_prompt=self.llm_chat.create_user_prompt(
                    user_prompt=user_input,
                    current_time=user_timestamp
                ),
                history=history,
                thinking=model.thinking
            )

            self.ui.print_conversation(response, role=Role.ASSISTANT)
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

        except AuthenticationError:
            self.ui.print_error("Invalid API key or credentials.")
            self.logger.error("Error during sending request to model: Authentication failed.")
            return True

        except RateLimitError:
            self.ui.print_error("Rate limit exceeded. Please try again later.")
            self.logger.error("Error during sending request to model: Rate limit exceeded.")
            return True

        except BadRequestError as e:
            model = self.model_config.get_model(self.session_manager.current_session.model)
            model_id = model.model_id if model is not None else "Unknown Model"

            self.ui.print_error(f"The model \"{model_id}\" is not available or the request was invalid.")
            self.logger.error(f"Error during sending request to model: Bad request - {str(e)}")
            return True

        except Exception as e:
            self.ui.print_error(f"Unexpected error occurred. Please check the logs for more details.")
            self.logger.error(f"Unexpected error during main loop: {str(e)}", exc_info=True)
            return False

    async def handle_user_input(self, user_input: str):
        """Handle user input from the chat UI, determining whether it is a command or a message to the LLM and processing it accordingly.

        Args:
            user_input (str): The raw user input string from the chat UI.
        """
        # Check if input is currently blocked (e.g., while processing a command or waiting for an LLM response). If it is blocked, inform the user and ignore the input.
        if self.is_input_blocked:
            self._update_status_and_info(additional_info="Input is currently blocked.")
            return

        # Set input block to prevent processing new inputs while the current input is being processed (either as a command or an LLM response).
        self.is_input_blocked = True

        # Check if user input is a command
        if self.command_handler.is_command(user_input):
            self.ui.start_waiting_indicator("Processing command...")
            success = await self._process_command(user_input)
            self.ui.stop_waiting_indicator()

            self.is_input_blocked = False

            # If processing the command indicates that the application should exit (e.g., the user entered the exit command), then call the UI's exit_app method to close the application.
            if not success:
                self.ui.exit_app()

            # Update the information message in the chat UI to reflect any changes that may have occurred as a result of processing the command (e.g., session change, model change, etc.).
            self._update_status_and_info()

            return

        # If it's not a command, process it as a message to the LLM
        self.ui.start_waiting_indicator("Waiting for response...")
        success = await self._process_llm_response(user_input)
        self.ui.stop_waiting_indicator()

        self.is_input_blocked = False

        # If processing the LLM response indicates that the application should exit (e.g., due to an unrecoverable error), then call the UI's exit_app method to close the application.
        if not success:
            self.ui.exit_app()

    def start_chat(self):
        """ Start an interactive chat session with the AI assistant.
        """
        self.logger.info("Starting chat application.")

        # Load new session on start
        self.logger.info("New chat session created.")
        self.session_manager.create_session(model=self.main_config.config.default_model)

        # Run the chat UI application
        self.ui.start_app(
            info_message="Type your message or command (type '/help' for available commands).",
            status_message=self._create_status_message(
                model_name=self.session_manager.current_session.model,
                session_title=self.session_manager.current_session.title
            )
        )

        # Save conversation history on exit
        session_data = self.session_manager.current_session
        if session_data is not None:
            self.history_storage.save_history(session_data)
            self.logger.info("Chat session ended and history saved.")

        self.ui.print_exit()

def main():
    """ Main function to start the chat application."""
    # Load environment variables from the .env file
    # This is necessary to ensure that any required API keys or configurations are available.
    # Please check LiteLLM documentation for more details on required environment variables.
    dotenv.load_dotenv()

    # Initialize the ChatApp and start the chat session.
    chat_app = ChatApp()
    chat_app.start_chat()
