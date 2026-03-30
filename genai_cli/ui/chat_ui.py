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
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich import print
from asyncio import create_task, sleep
from collections.abc import Coroutine
from io import StringIO
from dataclasses import dataclass

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
class ChatLine:
    """Represents a line in the chat log, which may contain markdown content.

    Attributes:
        content (str): The content of the chat line, which can be plain text or markdown-formatted text.
        is_markdown (bool): A flag indicating whether the content should be treated as markdown.
    """
    content: str
    is_markdown: bool = False

class ChatUI:
    """GenAI CLI Chat UI built with prompt_toolkit.

    Attributes:
        chat_log (list[ChatLine]): A list to store any output messages that should be displayed in the output field.
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
        self.chat_log: list[ChatLine] = []
        self.output_cursor_line = 0
        self.output_field = Window(
            content=FormattedTextControl(
                text=self._repaint_output,
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

    def _repaint_output(self) -> ANSI:
        """Repaint the output field by converting the chat log messages to ANSI format and returning them as a single ANSI string for display.

        Returns:
            ANSI: An ANSI-formatted string containing all the messages in the chat log, ready to be displayed in the output field.

        Notes:
            The cursor line is clamped when repainting.
        """
        output_messages = "\n".join(self._convert_rich_messages_to_ansi())
        self._clamp_cursor()
        return ANSI(output_messages)


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
        """Calculate the maximum cursor line based on the number of lines in the output field.

        Returns:
            int: The maximum cursor line number.
        """
        return max(0, len("\n".join(self._convert_rich_messages_to_ansi()).splitlines()) - 1)

    def _clamp_cursor(self):
        """Clamp the outpur cursor line to ensure it stays within the valid range of lines in the output field, preventing scrolling beyond the available content.
        """
        self.output_cursor_line = min(max(0, self.output_cursor_line), self._max_cursor_line())

    def _convert_rich_messages_to_ansi(self) -> list[str]:
        """Convert the messages in the chat log, which may contain Rich-formatted text, into ANSI-formatted strings for display in the output field.

        Returns:
            list[str]: A list of ANSI-formatted strings.
        """
        ansi_messages = []
        for message in self.chat_log:
            buf = StringIO()

            if message.is_markdown:
                message_content = Markdown(message.content)
            else:
                message_content = message.content

            Console(file=buf, force_terminal=True).print(message_content)
            ansi_messages.append(buf.getvalue())

        return ansi_messages

    def _scroll_to_bottom(self):
        """Scroll the output field to the bottom to show the most recent messages.

        Notes:
            A repaint trigger is sent after this method is called to ensure that the output field updates its display to reflect the new scroll position.
        """
        self.output_cursor_line = self._max_cursor_line()
        self.app.invalidate()

    def _print(self, message: str):
        """Print a message to the output field. If the application is not running, print to the stardard output instead.

        Args:
            message (str): The message to print.

        """
        if self.app.is_running:
            self.chat_log.append(ChatLine(content=message))
            # Scroll to the bottom after printing a message.
            self._scroll_to_bottom()
        else:
            print(message)

    def _print_markdown(self, markdown_message: str):
        """Print a markdown-formatted message to the output field. If the application is not running, print to the standard output instead.

        Args:
            markdown_message (str): The markdown-formatted message to print.
        """
        if self.app.is_running:
            self.chat_log.append(ChatLine(content=markdown_message, is_markdown=True))
            # Scroll to the bottom after printing a markdown message.
            self._scroll_to_bottom()
        else:
            print(Markdown(markdown_message))

    def print_conversation(self, message: str, role: Role):
        """Print a conversation message to the output field with appropriate formatting based on the role (user or assistant).

        Args:
            message (str): The message content.
            role (Role): The role of the message sender (e.g., Role.USER or Role.ASSISTANT) to determine formatting.
        """
        message = escape(message)
        match role:
            case Role.USER:
                self._print(f"[bold blue]{message}[/bold blue]")
            case Role.ASSISTANT:
                self._print_markdown(f"{message}")
            case _:
                self._print(f"{message}")

    def print_error(self, error_message: str):
        """Print an error message to the output field with error formatting.

        Args:
            error_message (str): The error message.
        """
        self._print(f"[bold red]Error: [/bold red]{error_message}")

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
        self._print(f"[on bright_black] [yellow]{command_prompt}[/yellow] [/on bright_black][bright_black][/bright_black]")
        self._print(command_output)

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
