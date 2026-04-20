from typing_extensions import override
from typing import Callable
from rich.markup import escape

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.core.session import Session
from genai_cli.core.history import History

class SessionsCommand(BaseCommand):
    """ Command to display all sessions.
    """
    name = "sessions"
    description = "Display all conversations."
    usage = "/sessions"

    def __init__(
        self,
        get_current_session_callback: Callable[[], Session|None],
        get_histories_callback: Callable[[], list[History]]
    ):
        super().__init__()
        self.get_current_session_callback: Callable[[], Session|None] = get_current_session_callback
        self.get_histories_callback: Callable[[], list[History]] = get_histories_callback

    def _list_histories(self) -> list[str]:
        """Helper method to format the list of chat histories for display.

        Returns:
            str: A formatted string listing all chat histories, with the current session highlighted.
        """
        if self.get_current_session_callback() is None:
            return [
                f"[command-list]{index}. [/command-list][command-output]{escape(history.title)}[/command-output]"
                for index, history in enumerate(self.get_histories_callback())
            ]

        return [
            f"[command-list]{index}. [/command-list][command-output-emphasis]{escape(history.title)} (current)[/command-output-emphasis]"
            if history.filename == self.get_current_session_callback().filename
            else f"[command-list]{index}. [/command-list][command-output]{escape(history.title)}[/command-output]"

            for index, history in enumerate(self.get_histories_callback())
        ]

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the sessions command to display all chat histories.

        Returns:
            str: A formatted string listing all chat histories, with the current session highlighted.
        """
        match argc:
            case 1:
                if not self.get_histories_callback():
                    return "[command-output]No conversations found.[/command-output]"

                # Format the list of chat histories for display, highlighting the current session if it exists.
                history_list = self._list_histories()
                history_list.insert(
                    0,
                    "[command-header]Conversations:[/command-header]"
                )

                return "\n".join(history_list)
            case _:
                raise CommandError(f"The '/{self.name}' command does not take any arguments.")

    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the sessions command. This command does not have any subcommands, so this method is left empty.
        """
        pass

    @override
    def get_options(self) -> list[str]:
        """This command does not have any options, so this method returns an empty set.

        Returns:
            list[str]: An empty set, as the sessions command does not have any options.
        """
        return []
