from typing_extensions import override
from typing import Callable
from rich.markup import escape

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError

class HelpCommand(BaseCommand):
    """Command to display help information about available commands.
    """
    name = "help"
    description = "Show this help message."
    usage = "/help [command]"

    def __init__(
        self,
        get_main_commands_callback: Callable[[], dict[str, BaseCommand]]
    ):
        super().__init__()
        self.get_main_commands_callback: Callable[[], dict[str, BaseCommand]] = get_main_commands_callback

    @override
    def get_options(self) -> list[str]:
        """Get the list of available command options. For the help command, this returns the list of all registered command names.
        """
        return list(self.get_main_commands_callback().keys())

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Display help information for the specified command or all commands if no specific command is provided.

        Returns:
            str: A help message for all commands.
        """
        match argc:
            case 1:
                return self._generate_help()
            case 2:
                if argv[1] in self.get_main_commands_callback():
                    command = self.get_main_commands_callback()[argv[1]]
                    return f"[command-output]Usage: {escape(command.usage)}[/command-output]"
                else:
                    raise CommandError(f"Unknown command '/{argv[1]}'. Use '/help' to see all available commands.")
            case _:
                raise CommandError(f"Too many arguments for the '/{self.name}' command.")

    def _generate_help(self) -> str:
        """Generate a help message for all available commands.

        Returns:
            str: A formatted help message listing all commands and their descriptions.
        """
        help_message = [
            f"[command-list]* [/command-list][command-output]{command.usage}: {command.description}[/command-output]"
            for command in self.get_main_commands_callback().values()
        ]
        help_message.insert(0, "[command-header]Available commands:[/command-header]")

        return "\n".join(help_message)

    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the help command. This command does not have any subcommands, so this method is left empty.
        """
        pass

