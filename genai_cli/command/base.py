class CommandError(Exception):
    """Custom exception class for command-related errors. This exception can be raised when there is an issue with executing a command, such as invalid arguments, missing required parameters, or any other error that occurs during command execution.
    """
    pass

class ExitError(Exception):
    """
    A custom exception class for termination-related errors. It can be used as a signal for application termination, such as when the user executes the “exit” command.
    However, it should not be used when the application terminates due to errors, such as unhandled exceptions or critical failures. In such cases, a separate exception must be thrown to indicate termination due to an error state.
    """
    pass

class BaseCommand:
    """Base class for all commands in the CLI application.
    This class defines the common structure and behavior for all commands.

    Attributes:
        name (str): The name of the command.
        description (str): A brief description of what the command does.
        usage (str): A string describing how to use the command.
        subcommands (dict[str, BaseCommand]): A dictionary mapping subcommand names to their corresponding command classes. This allows for hierarchical command structures where a command can have nested subcommands.
    """
    name: str
    description: str
    usage: str

    def __init__(self):
        """
        """
        self.subcommands: dict[str, 'BaseCommand'] = dict()
        self._register_all_subcommands()

    def _register_all_subcommands(self):
        """Register all subcommands for the current command. This method should be overridden by subclasses to register specific subcommands.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.

        Example:
            If a command has subcommands "sub1" and "sub2", the implementation of this method in the subclass would look like this:

            ```python
            def _register_all_subcommands(self):
                try:
                    self._register_subcommand(Sub1Command())
                    self._regisiter_subcommand(Sub2Command())
                except ValueError as e:
                    # Handle the error, such as logging it or re-raising it with additional context
                    logging.Logger.error(f"Failed to register subcommand: {e}")

            ```
        """
        raise NotImplementedError("The _register_all_subcommands method must be implemented by subclasses.")

    def register_subcommand(self, subcommand: 'BaseCommand'):
        """Register a subcommand to the current command.

        Args:
            subcommand (BaseCommand): The subcommand to be registered.

        Raises:
            ValueError: If a subcommand with the same name is already registered.
        """
        if subcommand.name in self.subcommands:
            raise ValueError(f"Subcommand '{subcommand.name}' is already registered for command '{self.usage}'.")

        self.subcommands[subcommand.name] = subcommand

    def get_options(self) -> list[str]:
        """Get a list of options for the command. This method should be overridden by subclasses to provide specific options for the command.

        Returns:
            list[str]: A list of options for the command. The options can be used for auto-completion in the chat UI.
        """
        raise NotImplementedError("The get_options method must be implemented by subclasses.")

    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the command. This method should be overridden by subclasses to provide specific functionality.

        Args:
            argc (int): The number of arguments passed to the command.
            argv (list[str]): A list of arguments passed to the command. The first element is typically the command name itself.

        Returns:
            str: The result of executing the command. The arguments contain the command name as the first element.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
            CommandError: If there is an error in executing the command, such as invalid arguments or missing required parameters.

        Notes:
            For example, if the command is "/cmd arg1 arg2", then argc would be 3 and argv would be ["cmd", "arg1", "arg2"].
        """
        raise NotImplementedError("The execute method must be implemented by subclasses.")

