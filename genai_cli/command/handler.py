import logging
import shlex

from genai_cli.command.base import CommandError
from genai_cli.command.registry import CommandRegistry
from genai_cli.const import COMMAND_PREFIX

class CommandHandler:
    """
    CommandHandler is responsible for managing and executing commands in the application. It maintains a registry of available commands and provides methods to check if an input is a command, parse command strings, and execute commands based on user input.

    Attributes:
        logger (logging.Logger): A logger instance for logging command execution and related information.
        command_registry (CommandRegistry): An instance of CommandRegistry that contains all registered commands. This allows the CommandHandler to access and execute the commands as needed.
    """

    def __init__(self, logger: logging.Logger, command_registry: CommandRegistry):
        """
        Initialize the CommandHandler with a logger.
        Args:
            logger (logging.Logger): A logger instance for logging command execution and related information.
            command_registry (CommandRegistry): An instance of CommandRegistry that contains all registered commands. This allows the CommandHandler to access and execute the commands as needed.
        """
        self.logger = logger
        self.command_registry = command_registry

    def is_command(self, user_input: str) -> bool:
        """Check if the input is a command.

        Args:
            user_input (str): The user input to check.

        Returns:
            bool: True if the input is a command, False otherwise.
        """
        return user_input.startswith(COMMAND_PREFIX)

    def parse_command(self, command: str) -> tuple[int, list[str]]:
        """Parse a command string into the number of arguments and a list of arguments.

        Args:
            command (str): The command string to parse.

        Returns:
            tuple[int, list[str]]: A tuple containing the number of arguments and a list of arguments.

        Note:
            The command and its arguments are separated by spaces, but quoted strings are treated as single arguments. For example, the command '/greet "John Doe"' would be parsed into `(2, ['greet', 'John Doe'])`.
        """

        # Remove the command prefix
        if command.startswith(COMMAND_PREFIX):
            command = command[len(COMMAND_PREFIX):]

        # Split the command into parts
        try:
            parts = shlex.split(command)
        except ValueError as e:
            self.logger.error(f"Error parsing command: {e}")
            return 0, []

        return len(parts), parts

    def handle_command(self, argc: int, argv: list[str]) -> str:
        """Handle a command based on the number of arguments and the list of arguments.

        Args:
            argc (int): The number of arguments in the command.
            argv (list[str]): The list of arguments in the command.

        Returns:
            str: The result of executing the command.

        Raises: 
            CommandError: If there is an error in executing the command, such as invalid arguments or missing required parameters.
        """
        # Check empty command
        if argc < 1:
            raise CommandError("No command provided.")

        # Check if the command exists
        command = self.command_registry.get_command(argv[0])
        if command is None:
            raise CommandError(f"Unknown command '/{argv[0]}'. Use '/help' to see all available commands.")

        # Execute the command
        self.logger.debug(f"Executing command: {argv}")
        try:
            result_message = command.execute(argc=argc, argv=argv)
        except CommandError as e:
            self.logger.error(f"Error executing command '{argv[0]}': {e}")
            raise

        return result_message

