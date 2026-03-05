from typing_extensions import override

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError, ExitError

class ExitCommand(BaseCommand):
    """Command to exit the application.
    """
    name = "exit"
    description = "Exit the application."
    usage = "/exit"

    def __init__(self):
        super().__init__()

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Exit the application.
        """
        match argc:
            case 1:
                raise ExitError("Exiting the application.")
            case _:
                raise CommandError(f"The '/{self.name}' command does not take any arguments.")

    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the exit command. This command does not have any subcommands, so this method is left empty.
        """
        pass

    @override
    def get_options(self) -> list[str]:
        """This command does not have any options, so this method returns an empty set.

        Returns:
            list[str]: An empty set, as the exit command does not have any options.
        """
        return []
