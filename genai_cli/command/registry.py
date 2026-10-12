import logging

from genai_cli.command.base import BaseCommand

class CommandRegistry:
    """ CommandRegistry is responsible for managing the registration and retrieval of commands in the application. It maintains a dictionary of command names and their corresponding command instances, allowing for easy access and execution of commands based on user input.

    Attributes:
        logger (logging.Logger): A logger instance for logging command registration and related information.
    """
    def __init__(
        self,
        logger:logging.Logger,
    ):
        self.logger = logger
        self.commands: dict[str, BaseCommand] = {}

    def register(self, command: BaseCommand):
        """Register a command to the registry.

        Args:
            command (BaseCommand): The command to be registered.

        Raises:
            ValueError: If a command with the same name is already registered.
        """
        if command.name in self.commands:
            raise ValueError(f"Command '{command.name}' is already registered.")

        self.commands[command.name] = command

    def get_command(self, name: str) -> BaseCommand | None:
        """Get a command by its name.

        Args:
            name (str): The name of the command to retrieve.

        Returns:
            BaseCommand | None: The command instance if found, otherwise None.
        """
        return self.commands.get(name)
