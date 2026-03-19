from prompt_toolkit.application import Application
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.completion import Completer
from typing import Callable
from rich.console import Console
from asyncio import create_task, sleep
from collections.abc import Coroutine

from genai_cli.ui.style import STYLE
from genai_cli.enums import Role
from genai_cli.core.session import Message

welcome_message = "\n".join([
    "",
    "[bold blue]____ ____ _  _ ____ _    ____ _    _[/bold blue]",
    "[bold blue]| __ |___ |\\ | |__| | __ |    |    |[/bold blue]",
    "[bold blue]|__] |___ | \\| |  | |    |___ |___ |[/bold blue]",
    "",
    "Welcome to GenAI CLI!",
    "Type /help for a list of available commands.",
    ""
])

exit_message = "\n".join([
    "",
    "[bold red]Thank you for using GenAI CLI![/bold red]",
    "[bold red]Goodbye![/bold red]",
    ""
])

spinner_frames = ["-", "\\", "|", "/"]

class ChatUI:
    """GenAI CLI Chat UI built with prompt_toolkit.

    Attributes:
        input_field (TextArea): Allows the user to type their messages and commands.
        waiting_message_field (Window): Displays a waiting indicator spinner when the applicatoin is in a waiting state (e.g., waiting for a response from the model).
        vi_mode_field (Window): Displays the current Vi mode (e.g., NORMAL, INSERT, REPLACE) in a fixed-width area.
        info_field (TextArea): Displays additional information such as the current model or tips for using the CLI.
        input_container (HSplit): A container that organizes the input field and info field vertically, separated by horizontal lines.
        on_submit (Callable[[str], Coroutine]): A callback function that is called when the user submits input, receiving the input string as an argument.
        bindings (KeyBindings): Defines key bindings for user interactions (e.g., submitting input, exiting the app).
        console (Console): A Rich Console instance for printing formatted output to the terminal.
        is_waiting (bool): A flag indicating whether the application is currently in a waiting state.
        spinner_index (int): An index to track the current frame of the waiting indicator spinner.
        waiting_message (str): An optional message to display alongside the waiting indicator spinner.
        app (Application): The prompt_toolkit Application instance that runs the UI.

    Notes:
        Output to the terminal (methods beginning with "print_") can be executed even before calling `start_app()`.
    """

    def __init__(self, completer: Completer, on_submit: Callable[[str], Coroutine]):
        """Initialize the ChatUI with its components and layout.

        Args:
            completer (Completer): A prompt_toolkit Completer for providing command completions in the input field.
            on_submit (Callable[[str], Coroutine]): A callback function that is called when the user submits input, receiving the input string as an argument.
        """
        # Initialize the input field for user messages and commands, and the info field for displaying the current Vi mode and additional information.
        self.input_field = TextArea(
            style="class:input-field",
            dont_extend_height=True,
            prompt="> ",
            multiline=True,
            completer=completer,
            complete_while_typing=True,
        )
        self.waiting_indicator_field = Window(
            content=FormattedTextControl(
                text=self._get_waiting_indicator
            ),
            height=1
        )
        self.vi_mode_field = Window(
            content=FormattedTextControl(
                text=self._get_vi_mode
            ),
            width=16,
            height=1
        )
        self.info_field = TextArea(
            style="class:info-field",
            text="",
            focusable=False,
            read_only=True,
            height=1
        )

        self.input_container = HSplit([
            self.waiting_indicator_field,
            Window(height=1, char="─", style="class:separator"),
            self.input_field,
            Window(height=1, char="─", style="class:separator"),
            VSplit([
                self.vi_mode_field,
                self.info_field
            ])
        ])

        # Set up key bindings for the application.
        self.bindings = KeyBindings()
        self.bindings.add("c-c")(lambda event: self.exit_app())

        # Store the on_submit callback function for handling user input when the Enter key is pressed.
        self.on_submit = on_submit
        self.input_field.accept_handler = self._accept_input

        # Initialize a Rich Console for printing formatted output to the terminal.
        self.console = Console()

        # Initialize state variables for managing the waiting indicator spinner.
        self.is_waiting = False
        self.spinner_index = 0
        self.waiting_message = ""

        # Create the prompt_toolkit Application with the defined layout, key bindings, style, and editing mode.
        self.app = Application(
            layout=Layout(
                container=self.input_container,
                focused_element=self.input_field
            ),
            key_bindings=self.bindings,
            style=STYLE,
            full_screen=False,
            editing_mode=EditingMode.VI,
        )

    def _accept_input(self, buffer: Buffer):
        """Handle user input when the Enter key is pressed. Args: buffer (Buffer): The input buffer containing the user's message.
        """
        user_input = buffer.text.strip()

        if user_input:
            create_task(self.on_submit(user_input))

    def _get_vi_mode(self) -> FormattedText:
        """Get the current Vi mode and return it as formatted text for display in the info field."""
        match self.app.vi_state.input_mode:
            case InputMode.NAVIGATION:
                return FormattedText([("class:vi-mode-normal", "-- NORMAL --")])
            case InputMode.INSERT | InputMode.INSERT_MULTIPLE:
                return FormattedText([("class:vi-mode-insert", "-- INSERT --")])
            case InputMode.REPLACE | InputMode.REPLACE_SINGLE:
                return FormattedText([("class:vi-mode-replace", "-- REPLACE --")])

    def _get_waiting_indicator(self) -> FormattedText | str:
        """Get the current frame of the waiting indicator spinner based on the spinner index."""
        if self.is_waiting:
            return FormattedText([("class:waiting-indicator", spinner_frames[self.spinner_index] + " " + self.waiting_message)])
        else:
            return ""

    async def _animate_waiting_indicator(self):
        """Animate a waiting indicator spinner in the wating_indicator_field while the application is in a waiting state."""
        i = 0
        while self.is_waiting:
            self.spinner_index = i % len(spinner_frames)
            self.app.invalidate()
            i += 1
            await sleep(0.1)

    def _print(self, message: str):
        """Print a message to the terminal, ensuring that it is displayed correctly whether the prompt_toolkit application is running or not.

        Args:
            message (str): The message to print.

        """
        if self.app.is_running:
            run_in_terminal(lambda: self.console.print(message + "\n"))
        else:
            self.console.print(message + "\n")

    def print_conversation(self, message: str, role: Role):
        """Print a conversation message to the output field with appropriate formatting based on the role (user or assistant).

        Args:
            message (str): The message content.
            role (Role): The role of the message sender (e.g., Role.USER or Role.ASSISTANT) to determine formatting.
        """
        match role:
            case Role.USER:
                self._print(f"[gray58]> {message}[/gray58]")
            case Role.ASSISTANT:
                self._print(f"{message}")
            case _:
                self._print(f"{message}")

    def print_error(self, error_message: str):
        """Print an error message to the output field with error formatting.

        Args:
            error_message (str): The error message.
        """
        self._print(f"[bold red]Error: [/bold red]{error_message}")

    def print_command_output(self, command_output: str):
        """Print command output to the output field with appropriate formatting.

        Args:
            command_output (str): The output from a command.
        """
        self._print(f"{command_output}")

    def print_histories(self, histories: list[Message]):
        """Print a list of conversation histories to the output field, formatting each message based on its role.

        Args:
            histories (list[Message]): A list of Message objects representing the conversation history.
        """
        for message in histories:
            self.print_conversation(message.content, message.role)

    def create_info_message(
        self,
        model_name: str | None = None,
        session_title: str | None = None,
        additional_info: str | None = None
    ) -> str:
        """Create an info message string based on the current model name, session title, and any additional information.

        Args:
            model_name (str | None): The name of the current model being used in the conversation.
            current_session_title (str | None): The title of the current conversation session.
            additional_info (str | None): Any additional information to include in the info message.
        """
        info_parts: list[str] = []
        if model_name:
            info_parts.append(f"[Model] {model_name}")
        if session_title:
            info_parts.append(f"[Session] {session_title}")
        if additional_info:
            info_parts.append(additional_info)

        return " | ".join(info_parts)

    def update_info(
        self,
        info_message: str,
    ):
        """Update the info field with a new info message.

        Args:
            info_message (str): The new info message to display in the info field.
        """
        self.info_field.text = info_message

    def print_welcome(self):
        """Print the welcome message to the terminal when the application starts."""
        self._print(welcome_message)

    def print_exit(self):
        """Print the exit message to the terminal when the application is exiting."""
        self._print(exit_message)

    def start_waiting_indicator(
        self,
        waiting_message: str = ""
    ):
        """Start the waiting indicator spinner with an optional message.

        Args:
            waiting_message (str): An optional message to display alongside the waiting indicator spinner.
        """
        self.waiting_message = waiting_message
        self.is_waiting = True

        create_task(self._animate_waiting_indicator())

    def stop_waiting_indicator(self):
        """Stop the waiting indicator spinner and clear any waiting message."""
        self.is_waiting = False
        self.spinner_index = 0
        self.waiting_message = ""
        self.app.invalidate()

    def start_app(
        self,
        info_message: str | None = None
    ):
        """Start the prompt_toolkit application to run the chat UI.

        Args:
            info_message (str | None): An optional message to display in the info field when the application starts. If provided, the info field will be updated with this message before the application runs.
        """
        if info_message is not None:
            self.app.run(pre_run=lambda: self.update_info(info_message=info_message))
        else:
            self.app.run()

    def exit_app(self):
        """Exit the application gracefully by resetting the input container to prevent further input and updates, and then calling the app's exit method."""
        # Remove input and info fields from the container to prevent further input and updates.
        self.input_container.children = []
        self.app.exit()
