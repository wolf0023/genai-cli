from rich.console import Console
from rich.markdown import Markdown
from rich.status import Status
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding.vi_state import InputMode

from session import Message
from enums import Role

class ChatUI:
    """ Chat UI class for rendering messages to the console.
    Attributes:
        console (Console): The rich console for rendering messages.
        prompt_session (PromptSession): The prompt session for user input.
    """
    def __init__(self):
        self.console = Console()
        self.prompt_session = PromptSession()

    def status_line_text(self, mode: InputMode) -> str:
        """ Get the status line for the chat UI.
        Args:
            mode (InputMode): The current input mode.
        """
        mode_map = {
            InputMode.INSERT: "INSERT",
            InputMode.INSERT_MULTIPLE: "INSERT MULTIPLE",
            InputMode.NAVIGATION: "NORMAL",
            InputMode.REPLACE: "REPLACE",
            InputMode.REPLACE_SINGLE: "REPLACE SINGLE",
        }
        mode_str = mode_map.get(mode, "UNKNOWN")

        return f"[mode: {mode_str}] [Press Ctrl+C or Ctrl+D to exit]"

    def get_user_prompt(self) -> str:
        """ Prompt the user for input.
        Returns:
            str: The user's input.
        """
        while True:
            user_input = self.prompt_session.prompt(
                ">>> ",
                vi_mode=True,
                multiline=True,
                bottom_toolbar=self.status_line_text(
                    self.prompt_session.app.vi_state.input_mode
                ),
                prompt_continuation="... "
            ).strip()

            # if not empty, return input
            if user_input:
                return user_input

    def select_session(self, history_titles: list[str]):
        """ Select or create a conversation session.
        Args:
            history_titles (list[str]): List of conversation session titles.
        Returns:
            int|None: The index of the selected session, or None if creating a new session.
        """
        # If no history, skip selection
        if not history_titles:
            return None

        self.print_message("[bold green]Select a conversation session:[/bold green]")
        for idx, title in enumerate(history_titles):
            self.print_message(f"[{idx}] {title}")

        # Prompt user to select session
        choice = -1
        while True:
            try:
                choice = int(self.prompt_session.prompt("Enter session number (or -1 to create new): ").strip())
            except ValueError:
                self.print_error("Invalid choice.")
                continue

            # Load selected session
            # When choice is -1, create new session
            if -1 <= choice < len(history_titles):
                break

            self.print_error("Invalid choice.")

        # Skip loading if creating new session
        if choice == -1:
            return None

        return choice

    def print_error(self, message: str):
        """ Print an error message to the console.
        Args:
            message (str): The error message to print.
        """
        self.console.print("\n[bold red]Error:[/bold red]", message, "\n")

    def print_ai_message(self, message: str):
        """ Print an AI message to the console.
        Args:
            message (str): The AI message to print.
        """
        self.console.print("\n", Markdown(message, code_theme="github-dark"), "\n")

    def print_user_message(self, message: str):
        """ Print a user message to the console.
        Args:
            message (str): The user message to print.
        """
        lines = message.splitlines()
        formatted_message = ">>> " + "\n... ".join(lines)

        self.console.print(formatted_message)

    def print_exit_message(self):
        """ Print an exit message to the console.
        """
        self.console.print("\n[bold red]Exiting the chat. Goodbye![/bold red]\n")

    def print_session_history(self, messages: list[Message]):
        """ Print the conversation history to the console.
        Args:
            messages (str): A list of Message objects representing the conversation history.
        """
        self.console.print("\n[bold yellow]Loading conversation history...[/bold yellow]\n")

        for msg in messages:
            role = msg.role
            content = msg.content

            if role == Role.USER:
                self.print_user_message(content)
            elif role == Role.ASSISTANT:
                self.print_ai_message(content)

    def print_message(self, message: str):
        """ Print a generic message to the console.
        Args:
            message (str): The message to print.
        """
        self.console.print(message)

    def waiting_indicator(self) -> Status:
        """ Show a waiting indicator while generating a response.
        Returns:
            Status: A rich Status context manager.
        """
        return self.console.status("[bold green]Generating response...[/bold green]\n\n")
