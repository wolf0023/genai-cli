from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text.ansi import ANSI
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.completion import Completer
from prompt_toolkit.data_structures import Point
from typing import Callable
from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from asyncio import create_task, sleep
from collections.abc import Coroutine
from dataclasses import dataclass, field
from shutil import get_terminal_size

from genai_cli.ui.style import STYLE
from genai_cli.enums import Role
from genai_cli.core.session import Message
from genai_cli.const import SCROLL_AMOUNT

welcome_message = "\n".join([
    "[bold blue]____ ____ _  _ ____ _    ____ _    _[/bold blue]",
    "[bold blue]| __ |___ |\\ | |__| | __ |    |    |[/bold blue]",
    "[bold blue]|__] |___ | \\| |  | |    |___ |___ |[/bold blue]",
    "",
    "Welcome to GenAI CLI!",
    "Type /help for a list of available commands.",
])

exit_message = "\n".join([
    "[bold red]Thank you for using GenAI CLI![/bold red]",
    "[bold red]Goodbye![/bold red]",
])

spinner_frames = ["-", "\\", "|", "/"]

@dataclass
class ChatMessage:
    """Represents a message in the chat log, which can be either plain text or markdown-formatted content.

    Attributes:
        content (str): The content of the message, which can be plain text or markdown-formatted text.
        is_markdown (bool): A flag indicating whether the content is markdown-formatted.
    """
    content: str
    is_markdown: bool = False

@dataclass
class ChatUICache:
    """A cache class to store the chat log and other relevant information for the ChatUI.

    Attributes:
        chat_log (list[ChatMessage]): A list of ChatMessage objects representing any output messages that should be displayed in the output field.
        ansi_cache (list[str]): A list of ANSI-formatted strings that can be used to cache the converted output messages for efficient repainting of the output field.
        terminal_width (int): An integer to store the current width of the terminal. This is used to check whether the width has been changed.
        total_lines (int): An integer to store the total number of ansi lines in the output field. This is used to ensure the cursor line is clamped correctly when the terminal width changes or when new messages are printed, preventing scrolling beyond the available content.
    """
    chat_log: list[ChatMessage] = field(default_factory=list)
    ansi_cache: list[str] = field(default_factory=list)
    terminal_width: int = 0
    total_lines: int = 0

class ChatUI:
    """GenAI CLI Chat UI built with prompt_toolkit.

    Attributes:
        ui_cache (ChatUICache): An instance of ChatUICache to store the chat log and other relevant information for the ChatUI.
        output_cursor_line (int): An integer to track the current line position of the cursor in the output field for scrolling purposes.
        output_field (Window): A scrollable window that displays the conversation history and any output messages.
        input_field (TextArea): Allows the user to type their messages and commands.
        waiting_message_field (Window): Displays a waiting indicator spinner when the application is in a waiting state (e.g., waiting for a response from the model).
        vi_mode_field (Window): Displays the current Vi mode (e.g., NORMAL, INSERT, REPLACE) in a fixed-width area.
        status_field (TextArea): Displays the status bar. (e.g. the model name or title of the current session, or any other status information)
        info_field (TextArea): Displays additional information or messages to the user.
        input_container (HSplit): A container that organizes the input field and info field vertically, separated by horizontal lines.
        on_submit (Callable[[str], Coroutine]): A callback function that is called when the user submits input, receiving the input string as an argument.
        bindings (KeyBindings): Defines key bindings for user interactions (e.g., submitting input, exiting the app).
        console (Console): A Rich Console instance used for converting messages to ANSI format for display in the output field.
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
        self.ui_cache = ChatUICache()
        self.output_cursor_line = 0
        self.output_field = Window(
            content=FormattedTextControl(
                text=self._get_output_text,
                show_cursor=False,
                get_cursor_position=lambda: Point(0, self.output_cursor_line)
            ),
            wrap_lines=True,
            always_hide_cursor=True,
        )
        self.input_field = TextArea(
            style="class:input-field",
            dont_extend_height=True,
            prompt="",
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
        self.status_field = TextArea(
            style="class:status-field",
            text="",
            focusable=False,
            read_only=True,
            height=1,
            width=0
        )
        self.info_field = TextArea(
            style="class:info-field",
            text="",
            focusable=False,
            read_only=True,
            height=1,
            width=0
        )

        self.input_container = HSplit([
            self.output_field,
            self.waiting_indicator_field,
            Window(height=1, char="─", style="class:separator"),
            VSplit([
                Window(
                    content=FormattedTextControl("> "),
                    width=2
                ),
                self.input_field,
            ]),
            Window(height=1, char="─", style="class:separator"),
            VSplit([
                self.vi_mode_field,
                Window(),
                self.status_field
            ]),
            self.info_field
        ])

        # Set up key bindings for the application.
        self.bindings = KeyBindings()

        @self.bindings.add("c-c")
        def _(event):
            """Handle the Ctrl+C key binding to exit the application gracefully."""
            self.exit_app()

        @self.bindings.add("c-u")
        def _(event):
            info = self.output_field.render_info
            if info is not None:
                self.output_cursor_line = max(0, info.vertical_scroll - SCROLL_AMOUNT)
            else:
                self.output_cursor_line = max(0, self.output_cursor_line - SCROLL_AMOUNT)

            # Clamp the cursor line to ensure it stays within the valid range of lines in the output field after scrolling up.
            self._clamp_cursor()

        @self.bindings.add("c-d")
        def _(event):
            max_line = self._max_cursor_line()
            info = self.output_field.render_info
            if info is not None:
                bottom_line = info.vertical_scroll + info.window_height - 1
                self.output_cursor_line = min(max_line, bottom_line + SCROLL_AMOUNT)
            else:
                self.output_cursor_line = min(max_line, self.output_cursor_line + SCROLL_AMOUNT)

            # Clamp the cursor line to ensure it stays within the valid range of lines in the output field after scrolling down.
            self._clamp_cursor()

        # Initialize a Rich Console instance for converting messages to ANSI format for display in the output field.
        self.console = Console(force_terminal=True)

        # Store the on_submit callback function for handling user input when the Enter key is pressed.
        self.on_submit = on_submit
        self.input_field.accept_handler = self._accept_input

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
            full_screen=True,
            editing_mode=EditingMode.VI,
        )

    def _get_output_text(self) -> ANSI:
        """Get the current output text in ANSI format for display in the output field by joining the cached ANSI messages."

        Return:
            ANSI: The current output text in ANSI format for display in the output field.
        """
        self._repaint_output()
        return ANSI("\n".join(self.ui_cache.ansi_cache))

    def _repaint_output(
        self,
        force: bool = False
    ):
        """Repaint the output field by converting the cached chat log messages to ANSI format and joining them into a single string for display.

        Args:
            force (bool): A flag indicating whether to force a repaint by converting the chat log messages.

        Notes:
            The cursor line is clamped when repainting.
        """
        terminal_width = get_terminal_size().columns

        # If the terminal width has not changed since the last repaint and force is not set to True, we can skip the conversion and just update the total lines for cursor clamping.
        if not force and terminal_width == self.ui_cache.terminal_width:
            self.ui_cache.total_lines = len("\n".join(self.ui_cache.ansi_cache).splitlines())

            # Clamp the cursor line.
            self._clamp_cursor()

            return

        # Convert the chat log messages to ANSI format and cache the results and the terminal width for future repaints.
        ansi_messages = self._convert_rich_messages_to_ansi(self.ui_cache.chat_log)
        self.ui_cache.terminal_width = terminal_width
        self.ui_cache.ansi_cache = ansi_messages

        # Join the ANSI messages into a single string and update the total lines in the output for cursor clamping.
        self.ui_cache.total_lines = len("\n".join(ansi_messages).splitlines())

        # Clamp the cursor line.
        self._clamp_cursor()

    def _accept_input(self, buffer: Buffer):
        """Handle user input when the Enter key is pressed. Args: buffer (Buffer): The input buffer containing the user's message."""
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
        """Animate a waiting indicator spinner in the waiting_indicator_field while the application is in a waiting state."""
        i = 0
        while self.is_waiting:
            self.spinner_index = i % len(spinner_frames)
            self.app.invalidate()
            i += 1
            await sleep(0.1)

    def _max_cursor_line(self) -> int:
        """Return the maximum cursor line number based on the total number of lines in the output field.

        Returns:
            int: The maximum cursor line number.
        """
        return max(0, self.ui_cache.total_lines - 1)

    def _clamp_cursor(self):
        """Clamp the output cursor line to ensure it stays within the valid range of lines in the output field, preventing scrolling beyond the available content.
        """
        self.output_cursor_line = min(max(0, self.output_cursor_line), self._max_cursor_line())

    def convert_rich_message_to_ansi(
        self,
        message: str,
        is_markdown: bool = False
    ) -> str:
        """Convert a single message (either plain text or markdown-formatted) to an ANSI-formatted string using Rich's Console.

        Returns:
            str: An ANSI-formatted string.
        """
        if is_markdown:
            message_content = Markdown(message)
        else:
            message_content = message

        with self.console.capture() as capture:
            self.console.print(message_content)
        return capture.get()

    def _convert_rich_messages_to_ansi(
        self,
        messages: list[ChatMessage]
    ) -> list[str]:
        """Convert a list of messages (either plain text or markdown-formatted) to a list of ANSI-formatted strings using Rich's Console.

        Args:
            messages (list[ChatMessage]): A list of ChatMessage objects to be converted.

        Returns:
            list[str]: A list of ANSI-formatted strings corresponding to the input messages.
        """
        return [self.convert_rich_message_to_ansi(message.content, message.is_markdown) for message in messages]

    def _scroll_to_bottom(self):
        """Scroll the output field to the bottom to show the most recent messages.

        Notes:
            A repaint trigger is sent after this method is called to ensure that the output field updates its display to reflect the new scroll position.
        """
        self.output_cursor_line = self._max_cursor_line()
        self.app.invalidate()

    def print_message(
        self,
        message: str,
        is_markdown: bool = False
    ):
        """Print a message to the output field, converting it to ANSI format for display. If the application is not running, print directly to the terminal.

        Args:
            message (str): The message content to be printed, which can be either plain text or markdown-formatted text.
            is_markdown (bool): A flag indicating whether the message content is markdown-formatted.
        """
        if self.app.is_running:
            # Append the message to the chat log cache and convert it to ANSI format for display in the output field.
            self.ui_cache.chat_log.append(ChatMessage(content=message, is_markdown=is_markdown))
            self.ui_cache.ansi_cache.append(self.convert_rich_message_to_ansi(message=message, is_markdown=is_markdown))

            # Trigger a repaint to update the output field with the new message.
            self._repaint_output(force=True)

            # Scroll to the bottom after printing a message.
            self._scroll_to_bottom()
        else:
            # If the app is not running, we can print directly to the terminal whthout using the prompt_toolkit output field.
            print(message if not is_markdown else Markdown(message))

    def print_conversation(self, message: str, role: Role):
        """Print a conversation message to the output field with appropriate formatting based on the role (user or assistant).

        Args:
            message (str): The message content.
            role (Role): The role of the message sender (e.g., Role.USER or Role.ASSISTANT) to determine formatting.
        """
        message = escape(message)
        match role:
            case Role.USER:
                self.print_message(f"[bold blue]{message}[/bold blue]")
            case Role.ASSISTANT:
                self.print_message(f"{message}", is_markdown=True)
            case _:
                self.print_message(f"{message}")

    def print_error(self, error_message: str):
        """Print an error message to the output field with error formatting.

        Args:
            error_message (str): The error message.
        """
        self.print_message(f"[bold red]Error: [/bold red]{error_message}")

    def print_command_output(
        self,
        command_prompt: str,
        command_output: str
    ):
        """Print the command prompt and its output to the terminal.

        Args:
            command_prompt (str): The command that was executed, to be displayed as a prompt before the output.
            command_output (str): The output from a command.
        """
        command_prompt = escape(command_prompt)
        self.print_message(f"[on bright_black] [yellow]{command_prompt}[/yellow] [/on bright_black][bright_black][/bright_black]")
        self.print_message(command_output)

    def print_histories(self, histories: list[Message]):
        """Print a list of conversation histories to the output field, formatting each message based on its role.

        Args:
            histories (list[Message]): A list of Message objects representing the conversation history.
        """
        for message in histories:
            self.print_conversation(message.content, message.role)

    def update_status_bar(
        self,
        status_message: str
    ):
        """Update the status bar with a new message.

        Args:
            status_message (str): The message to display in the status bar.
        """
        self.status_field.text = status_message
        self.status_field.window.width = Dimension(
            preferred=len(status_message)+1,
            max=len(status_message)+1
        )
        self.app.invalidate()

    def update_info(
        self,
        info_message: str
    ):
        """Update the info field with a new message.

        Args:
            info_message (str): The message to display in the info field.
        """
        self.info_field.text = info_message
        self.info_field.window.width = Dimension(preferred=len(info_message), max=len(info_message))
        self.app.invalidate()

    def print_welcome(self):
        """Print the welcome message to the terminal when the application starts."""
        self.print_message(welcome_message)

    def print_exit(self):
        """Print the exit message to the terminal when the application is exiting."""
        print(exit_message)

    def start_waiting_indicator(
        self,
        waiting_message: str = ""
    ):
        """Start the waiting indicator spinner with an optional message.

        Args:
            waiting_message (str): An optional message to display alongside the waiting indicator spinner.
        """
        if not self.is_waiting:
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
        info_message: str | None = None,
        status_message: str | None = None
    ):
        """Start the prompt_toolkit application to run the chat UI.

        Args:
            info_message (str | None): An optional message to display in the info field when the application starts.
            status_message (str | None): An optional message to display in the status bar when the application starts.
        """
        # Define a pre-run function to update the info and status bar with the provided messages before the application starts.
        def pre_run():
            if info_message is not None:
                self.update_info(info_message)
            if status_message is not None:
                self.update_status_bar(status_message)

            self.print_welcome()

        self.app.run(pre_run=pre_run)

    def exit_app(self):
        """Exit the application gracefully by resetting the input container to prevent further input and updates, and then calling the app's exit method."""
        # Remove input and info fields from the container to prevent further input and updates.
        self.input_container.children = []
        self.app.exit()
