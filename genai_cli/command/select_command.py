from typing_extensions import override
from typing import Callable
from rich.markup import escape

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.core.history import History
from genai_cli.core.session import Session

class SelectCommand(BaseCommand):
    """ Command to select an existing conversation.
    """
    name = "select"
    description = "Select a conversation to continue."
    usage = "/select [conversation_id]"

    def __init__(
        self,
        get_histories_callback: Callable[[], list[History]],
        get_history_callback: Callable[[str], Session],
        load_session_callback: Callable[[Session], None],
        get_current_session_callback: Callable[[], Session]
    ):
        super().__init__()
        self.get_histories_callback: Callable[[], list[History]] = get_histories_callback
        self.get_history_callback: Callable[[str], Session] = get_history_callback
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
                try:
                    conversation_id = int(argv[1])
                    conversation_filename = self.get_histories_callback()[conversation_id].filename

                    # Check if the selected conversation is already the current session
                    if self.get_current_session_callback().filename == conversation_filename:
                        raise CommandError(f"Conversation '{self.get_current_session_callback().title}' is already selected.")

                    session = self.get_history_callback(conversation_filename)
                    self.load_session_callback(session)

                    return f"[command-output]Conversation '{escape(session.title)}' selected.[/command-output]"
                except (ValueError, IndexError):
                    raise CommandError("Invalid conversation ID. Please provide a valid integer ID from the conversation list.")
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
        return []

