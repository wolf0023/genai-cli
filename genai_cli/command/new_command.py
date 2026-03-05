from typing_extensions import override
from typing import Callable

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.config.config import Config
from genai_cli.core.session import Session
from genai_cli.const import TITLE_MAX_LENGTH

class NewCommand(BaseCommand):
    """ Command to create a new conversation.
    """
    name = "new"
    description = "Create a new conversation with default model"
    usage = "/new \[title]"

    def __init__(
        self,
        main_config: Config,
        create_new_session_callback: Callable[..., Session]
    ):
        super().__init__()
        self.default_model = main_config.default_model
        self.create_new_session_callback = create_new_session_callback

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the new command to create a new conversation.

        Returns:
            str: A message indicating that a new conversation has been created.
        """
        match argc:
            case 1:
                self.create_new_session_callback(model=self.default_model)
                return "[bold green]New conversation created with default model.[/bold green]"
            case 2:
                if len(argv[1]) > TITLE_MAX_LENGTH:
                    raise CommandError(f"Title cannot exceed {TITLE_MAX_LENGTH} characters.")

                title = argv[1]
                self.create_new_session_callback(model=self.default_model, title=title)

                return f"[bold green]New conversation '{title}' created with default model.[/bold green]"
            case _:
                raise CommandError(f"Too many arguments for the '/{self.name}' command.")

    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the new command. This command does not have any subcommands, so this method is left empty.
        """
        pass

    @override
    def get_options(self) -> list[str]:
        """This command does not have any options, so this method returns an empty set.

        Returns:
            list[str]: An empty set, as the new command does not have any options.
        """
        return []
