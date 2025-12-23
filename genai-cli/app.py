from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding.vi_state import InputMode
from rich.console import Console
from rich.markdown import Markdown
from datetime import datetime
from litellm.exceptions import AuthenticationError, RateLimitError

from llm_chat import get_chat_response, create_user_prompt
from session import SessionManager, Session
from storage import HistoryStorage
from enums import Role

def get_vi_mode(mode: InputMode) -> str:
    """ Get the current vi mode as a string.
    """
    mode_map = {
        InputMode.INSERT: "INSERT",
        InputMode.INSERT_MULTIPLE: "INSERT MULTIPLE",
        InputMode.NAVIGATION: "NORMAL",
        InputMode.REPLACE: "REPLACE",
        InputMode.REPLACE_SINGLE: "REPLACE SINGLE",
    }
    return mode_map.get(mode, "UNKNOWN")

class ChatApp:
    """ Chat application class for managing the chat UI.
    Attributes:
        console (Console): Rich console for output.
        prompt_session (PromptSession): Prompt session for user input.
        session_manager (SessionManager): Manager for conversation sessions.
    """
    def __init__(self):
        self.console = Console()
        self.prompt_session = PromptSession()
        self.session_manager = SessionManager()
        self.history_storage = HistoryStorage()

    def status_line(self):
        """ Generate the status line for the chat UI."
        """
        vi_mode = get_vi_mode(self.prompt_session.app.vi_state.input_mode)
        return f"[Mode: {vi_mode}] [Press Ctrl+C or Ctrl+D to exit]"

    def select_session(self):
        """ Select or create a conversation session.
        """
        history_list = self.history_storage.get_history_titles()

        # If no history, skip selection
        if not history_list:
            return

        self.console.print("[bold green]Select a conversation session:[/bold green]")
        for idx, title in enumerate(history_list):
            self.console.print(f"[{idx}] {title}")

        # Prompt user to select session
        try:
            choice = int(self.prompt_session.prompt("Enter session number (or -1 to create new): ").strip())

            # Skip loading if creating new session
            if choice == -1:
                return

            # Load selected session
            if 0 <= choice < len(history_list):
                filename = self.history_storage.get_filename(choice)
                history_data = self.history_storage.get_history(filename)

                self.session_manager.load_session(
                    title=history_data["title"],
                    provider=history_data["provider"],
                    created_at=history_data["created_at"],
                    messages=history_data["messages"],
                    filename=filename
                )
                return

            # Invalid choice
            self.console.print("[bold red]Invalid choice.[/bold red]")

        except ValueError:
            self.console.print("[bold red]Invalid choice.[/bold red]")

    def print_session_history(self):
        """ Print the conversation history of the current session."
        """
        # Not print anything if no current session
        if self.session_manager.current_session is None:
            return

        # Print chat history
        self.console.print("\n[bold yellow]Loading conversation history...[/bold yellow]\n")

        messages = self.session_manager.current_session.messages
        for message in messages:
            role = message.role
            content = message.content
            if role == Role.USER:
                self.console.print(f">>> {content}")
            elif role == Role.ASSISTANT:
                self.console.print("\n[bold blue]AI:[/bold blue] ", Markdown(content), "\n")

    def main_loop(self) -> bool:
        """ Main chat loop for user interaction.
        Returns:
            bool: True to continue the chat, False to exit.
        """
        # Main chat loop
        try:
            # Get current session
            current_session: Session|None = self.session_manager.current_session
            if current_session is None:
                raise Exception("No active session found.")

            # Prompt user for input
            user_input = self.prompt_session.prompt(
                ">>> ",
                vi_mode=True,
                multiline=True,
                bottom_toolbar=self.status_line
            ).strip()
            if not user_input:
                return True

            user_timestamp = datetime.now()

            with self.console.status("[bold green]Generating response...[/bold green]\n\n"):
                # Get chat history
                session_data: dict = current_session.to_dict()
                history = session_data["messages"]

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

            self.console.print("\n[bold blue]AI:[/bold blue] ", Markdown(response), "\n")
            assistant_timestamp = datetime.now()

            # Append user message and AI response to session
            current_session.append_message(
                role=Role.USER,
                content=user_input,
                timestamp=user_timestamp
            )
            current_session.append_message(
                role=Role.ASSISTANT,
                content=response,
                timestamp=assistant_timestamp
            )

            return True

        except (KeyboardInterrupt, EOFError):
            # Exit on Ctrl+C or Ctryl+D
            return False

        except AuthenticationError:
            self.console.print("\n[bold red]Error:[/bold red] Invalid API key or credentials.\n")
            return False

        except RateLimitError:
            self.console.print("\n[bold red]Error:[/bold red] Rate limit exceeded. Please try again later.\n")
            return True

        except Exception as e:
            # When an error occurs, print it and continue
            self.console.print("\n[bold red]Error:[/bold red] ", str(e), "\n")
            return False

    def start_chat(self):
        """ Start an interactive chat session with the AI assistant.
        """
        try: 
            self.select_session()
            current_session = self.session_manager.current_session
        except (KeyboardInterrupt, EOFError):
            # Exit on Ctrl+C or Ctrl+D
            self.console.print("\n[bold red]Exiting the chat. Goodbye![/bold red]\n")
            return

        # Print existing conversation history
        self.print_session_history()

        # Create a new session if none selected
        if current_session is None:
            current_session = self.session_manager.create_session()

        # Start main chat loop
        continue_chat = True
        while continue_chat:
            continue_chat = self.main_loop()

        # Save conversation history on exit
        session_data = current_session.to_dict()
        self.history_storage.save_history(session_data, current_session.filename)
        self.console.print("\n[bold red]Exiting the chat. Goodbye![/bold red]\n")
        
if __name__ == "__main__":
    chat_app = ChatApp()
    chat_app.start_chat()
