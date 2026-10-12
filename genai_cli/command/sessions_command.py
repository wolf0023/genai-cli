from typing_extensions import override
from typing import Callable
from rich.markup import escape

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.core.session import Session

class SessionsCommand(BaseCommand):
    """ Command to display all sessions.
    """
    name = "sessions"
    description = "Display all conversations."
    usage = "/sessions"

    def __init__(
        self,
        get_current_session_callback: Callable[[], Session|None],
        get_sessions_callback: Callable[[], list[Session]]
    ):
        super().__init__()
        self.get_current_session_callback: Callable[[], Session|None] = get_current_session_callback
        self.get_sessions_callback: Callable[[], list[Session]] = get_sessions_callback

    def _list_sessions(self) -> list[str]:
        """Helper method to format the list of chat sessions for display.

        Returns:
            str: A formatted string listing all chat sessions, with the current session highlighted.
        """
        current_session: Session|None = self.get_current_session_callback()
        if current_session is None:
            return [
                f"[command-list]{session.id.hex[:8]}: [/command-list][command-output]{escape(session.title)}[/command-output]"
                for session in self.get_sessions_callback()[::-1]
            ]

        return [
            f"[command-list]{session.id.hex[:8]}: [/command-list][command-output-emphasis]{escape(session.title)} (current)[/command-output-emphasis]"
            if session.id == current_session.id
            else f"[command-list]{session.id.hex[:8]}: [/command-list][command-output]{escape(session.title)}[/command-output]"

            for session in self.get_sessions_callback()[::-1]
        ]

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the sessions command to display all chat sessions.

        Returns:
            str: A formatted string listing all chat sessions, with the current session highlighted.
        """
        match argc:
            case 1:
                if not self.get_sessions_callback():
                    return "[command-output]No conversations found.[/command-output]"

                # Format the list of chat sessions for display, highlighting the current session if it exists.
                history_list = self._list_sessions()
                history_list.insert(0, "[command-header]Conversations:[/command-header]")

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
