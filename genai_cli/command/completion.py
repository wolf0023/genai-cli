from prompt_toolkit.completion import Completer, Completion
from typing_extensions import override
from typing import Any, Generator
import logging

from genai_cli.command.registry import CommandRegistry
from genai_cli.command.base import BaseCommand

class CommandCompleter(Completer):
    """CommandCompleter is a custom completer for command auto-completion in the chat UI. It extends the prompt_toolkit's Completer class and provides completions based on a nested dictionary of commands and subcommands.

    Attributes:
        logger (logging.Logger): A logger instance for logging completion-related information.
        main_commands (dict[str, BaseCommand]): A dictionary mapping command names to their corresponding command instances. This allows the CommandCompleter to access the main commands and their subcommands to build the completions dictionary.
        completions (dict[str, Any | None] | None): A nested dictionary mapping command names to their corresponding completions.
    """

    def __init__(self, logger: logging.Logger, command_registry: CommandRegistry):
        """ Initialize the CommandCompleter with a logger and set up the completions based on the CommandHandler's main commands.
        Args:
            logger (logging.Logger): A logger instance for logging completion-related information.
            main_commands (dict[str, BaseCommand]): A dictionary mapping command names to their corresponding command instances. This allows the CommandCompleter to access the main commands and their subcommands to build the completions dictionary.
        """
        self.logger = logger
        self.main_commands: dict[str, BaseCommand] = command_registry.commands

    def _complete_main_commands(self, word: str) -> Generator[Completion, Any, None]:
        """Generate completions for main commands based on the current input word.

        Args:
            word (str): The current input word for which to generate completions.
        """
        for command_name in self.main_commands.keys():
            candidate = f"/{command_name}"
            if candidate.startswith(word):
                yield Completion(candidate, start_position=-len(word))

    def _traverse_to_current_command(self, parts: list[str]) -> BaseCommand | None:
        """Traverse the command hierarchy to find the current command context based on the input parts.

        Args:
            parts (list[str]): A list of command parts derived from the user's input. The first part is expected to be the main command, and subsequent parts may represent subcommands or options.

        Notes:
            For example, suppose there is a command "/cmd sub [opt1(option) | opt2(option)]".
            If the user types "/cmd sub opt", the variable `parts[1:]` will be ["sub", "opt"].
            Futhermore, the variable `command` is expected to contain "sub" command object.
        """
        command_name = parts[0][1:]  # Remove the leading "/"
        command = self.main_commands.get(command_name)

        for token in parts[1:]:
            if command is None:
                break

            # Check if the token is an option for the current command.
            options = command.get_options()
            if [opt for opt in options if opt.startswith(token)] == [token]:
                command = None
                break

            if token in command.subcommands:
                command = command.subcommands.get(token)

        return command

    def _complete_subcommands_and_options(self, command: BaseCommand, word: str) -> Generator[Completion, Any, None]:
        """Generate completions for subcommands and options of the current command context.

        Args:
            command (BaseCommand): The current command context for which to generate completions.
        """
        for subcommand_name in command.subcommands:
            if subcommand_name.startswith(word):
                yield Completion(subcommand_name, start_position=-len(word))

        for option in command.get_options():
            if option.startswith(word):
                yield Completion(option, start_position=-len(word))

    @override
    def get_completions(self, document, complete_event):
        text = document.text

        # Only provide completions for commands that start with "/".
        if not text.startswith("/"):
            return

        # Split the input text into parts to determine the current command and subcommand context.
        # For example, if the user types "/cmd sub", the parts will be ["/cmd", "sub"].
        parts = text.split()

        # If the user is typing the main command (e.g., "/cmd"), provide completions for main commands.
        if len(parts) == 1 and not text.endswith(" "):
            word = parts[0]
            # Iterate through the main commands and yield completions that match the current input.
            yield from self._complete_main_commands(word)
            return

        # Traverse the command hierarchy to find the current command context based on the input parts.
        command = self._traverse_to_current_command(parts)
        if command is None:
            return

        # Provide completions for subcommands and options of the current command context.
        word = document.get_word_before_cursor()
        yield from self._complete_subcommands_and_options(command, word)

