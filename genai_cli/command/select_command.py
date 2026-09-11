from typing_extensions import override
from typing import Callable
from rich.markup import escape

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.core.session import Session

class SelectCommand(BaseCommand):
    """ Command to select an existing conversation.
    """
    name = "select"
    description = "Select a conversation to continue."
    usage = "/select [conversation_id (UUID)]"

    def __init__(
        self,
        get_sessions_callback: Callable[[], list[Session]],
        load_session_callback: Callable[[Session], None],
        get_current_session_callback: Callable[[], Session]
    ):
        super().__init__()
        self.get_sessions_callback: Callable[[], list[Session]] = get_sessions_callback
        self.load_session_callback: Callable[[Session], None] = load_session_callback
        self.get_current_session_callback: Callable[[], Session] = get_current_session_callback

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the select command to load a conversation by its ID.

        Returns:
            str: A message indicating that the conversation has been loaded, or an error message if the conversation ID is invalid.
        """
        match argc:
            case 1:
                raise CommandError(f"Conversation ID is required. Usage: {self.usage}")
            case 2:
                conversation_id = str(argv[1])

                # Check if the selected conversation is already the current session
                if self.get_current_session_callback().id == conversation_id:
                    raise CommandError(f"Conversation '{self.get_current_session_callback().title}' is already selected.")

                # Check if the selected conversation exists
                session = next((
                    s
                    for s in self.get_sessions_callback()
                    if s.id.hex == conversation_id
                ), None)

                if session is None:
                    raise CommandError("Invalid conversation ID. Please provide a valid UUID from the conversation list.")

                self.load_session_callback(session)
                return f"[command-output]Conversation '{escape(session.title)}' selected.[/command-output]"
            case _:
                raise CommandError(f"Too many arguments for the '/{self.name}' command.")


    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the select command. This command does not have any subcommands, so this method is left empty.
        """
        pass

    @override
    def get_options(self) -> list[str]:
        """This command does not have any options, so this method returns an empty set.

        Returns:
            list[str]: An empty set, as the select command does not have any options.
        """
        return [s.id.hex for s in self.get_sessions_callback()]

