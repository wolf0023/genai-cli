from datetime import datetime
from litellm.exceptions import AuthenticationError, RateLimitError

from llm_chat import get_chat_response, create_user_prompt
from session import SessionManager
from history import HistoryStorage
from enums import Role
from chat_ui import ChatUI

class ChatApp:
    """ Chat application class for managing the chat UI.
    Attributes:
        console (Console): Rich console for output.
        prompt_session (PromptSession): Prompt session for user input.
        session_manager (SessionManager): Manager for conversation sessions.
    """
    def __init__(self):
        self.session_manager = SessionManager()
        self.history_storage = HistoryStorage()
        self.ui = ChatUI()

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

            with self.ui.waiting_indicator():
                # Get chat history
                history = self.session_manager.current_session.messages

                # Get AI response
                response = get_chat_response(
                    model="perplexity/sonar-pro",
                    system_prompt="You are a helpful AI assistant.",
                    user_prompt=create_user_prompt(
                        user_input, 
                        current_time=user_timestamp
                    ),
                    history=history,
                )

            self.ui.print_ai_message(response)
            assistant_timestamp = datetime.now()

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

            return True

        except (KeyboardInterrupt, EOFError):
            # Exit on Ctrl+C or Ctryl+D
            return False

        except AuthenticationError:
            self.ui.print_error("Invalid API key or credentials.")
            return False

        except RateLimitError:
            self.ui.print_message("Rate limit exceeded. Please try again later.")
            return True

        except Exception as e:
            # When an error occurs, print it and continue
            self.ui.print_error(str(e))
            return False

    def start_chat(self):
        """ Start an interactive chat session with the AI assistant.
        """
        try: 
            # Let user select a session from history
            choice = self.ui.select_session(self.history_storage.get_history_titles())
        except (KeyboardInterrupt, EOFError):
            # Exit on Ctrl+C or Ctrl+D
            self.ui.print_exit_message()
            return

        # Load selected session
        if choice is not None:
            # Get history data
            filename = self.history_storage.get_filename(choice)
            history_data = self.history_storage.get_history(filename)

            # Load session into session manager
            self.session_manager.load_session(history_data)

            # Print existing conversation history
            self.ui.print_session_history(self.session_manager.current_session.messages)
        else:
            # Create a new session if none selected
            self.session_manager.create_session()

        continue_chat = True
        while continue_chat:
            continue_chat = self.main_loop()

        # Save conversation history on exit
        session_data = self.session_manager.current_session
        self.history_storage.save_history(session_data)
        self.ui.print_exit_message()

if __name__ == "__main__":
    chat_app = ChatApp()
    chat_app.start_chat()
