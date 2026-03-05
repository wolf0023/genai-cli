from typing_extensions import override
from typing import Callable

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
        get_current_session_callback: Callable[[], Session],
        get_histories_callback: Callable[[], list[History]]
    ):
        """Initialize the ListCommand with the current session and chat histories.

        Args:
            get_current_session_callback (Callable): A callback function to retrieve the current session.
            get_histories_callback (list[History]): A callback function to get the list of conversation history.
        """
        super().__init__()
        self.get_current_session_callback: Callable[[], Session] = get_current_session_callback
        self.get_histories_callback: Callable[[], list[History]] = get_histories_callback

    def _list_histories(self) -> list[str]:
        """Helper method to format the list of chat histories for display.

        Returns:
            str: A formatted string listing all chat histories, with the current session highlighted.
        """
        if self.get_current_session_callback() is None:
            return [
                f"\[{index}] {history.title}"
                for index, history in enumerate(self.get_histories_callback())
            ]

        return [
            f"[yellow][{index}] {history.title} (current)[/yellow]"
            if history.filename == self.get_current_session_callback().filename
            else f"\[{index}] {history.title}"

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
                    return "No conversations found."

                # Format the list of chat histories for display, highlighting the current session if it exists.
                history_list = self._list_histories()
                history_list.insert(
                    0,
                    "[bold green]Conversations:[/bold green]"
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
