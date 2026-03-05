from prompt_toolkit.completion import Completer, Completion
from typing_extensions import override
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
            for command_name in self.main_commands.keys():
                candidate = f"/{command_name}"
                if candidate.startswith(word):
                    yield Completion(candidate, start_position=-len(word))

            return

        # For example, suppose there is a command "/cmd sub [test1 | test2]".
        # If the user types "/cmd sub tes", the variable `parts[1:]` will be ["sub", "tes"].
        # Futhermore, the variable `command` is expected to contain "sub" command object.
        command_name = parts[0][1:]  # Remove the leading "/"
        command = self.main_commands.get(command_name)

        for token in parts[1:]:
            if command is not None and token in command.subcommands:
                command = command.subcommands.get(token)
            else:
                break

        if command is None:
            return

        # In the above example, the variable `word` will be "tes".
        word = document.get_word_before_cursor()
        for subcommand_name in command.subcommands:
            if subcommand_name.startswith(word):
                yield Completion(subcommand_name, start_position=-len(word))

        for option in command.get_options():
            if option.startswith(word):
                yield Completion(option, start_position=-len(word))

