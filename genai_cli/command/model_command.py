from typing_extensions import override
from typing import Callable

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.config.model import Model

class ModelCommand(BaseCommand):
    """Command to change the model for the current session. 
    """
    name = "model"
    description = "Change the model for the current session"
    usage = "/model [model_name]"

    def __init__(
        self,
        models: list[Model],
        get_current_model_callback: Callable[[], str|None],
        change_model_callback: Callable[[str], None]
    ):
        super().__init__()
        self.model_names: list[str] = [model.model_name for model in models]
        self.get_current_model_callback: Callable[[], str|None] = get_current_model_callback
        self.change_model_callback: Callable[[str], None] = change_model_callback

    @override
    def get_options(self) -> list[str]:
        """Get the list of available model names.
        This is used for autocompletion when the user types the command.

        Returns:
            list[str]: A list of available model names.
        """
        return self.model_names

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the model command.
        If no arguments are provided, it will return the current model.
        If a model name is provided, it will change the current model to the specified one.
        """
        match argc:
            case 1:
                current_model: str|None = self.get_current_model_callback()
                if current_model is None:
                    return "[command-output]No session is currently loaded.[/command-output]"
                else:
                    return f"[command-output]Current model: '{current_model}'.[/command-output]"
            case 2:
                # Check whether a model exists
                if argv[1] not in self.model_names:
                    raise CommandError(f"The specified model could not be found.")

                self.change_model_callback(argv[1])
                return f"[command-output]Model changed to '{argv[1]}'.[/command-output]"

            case _:
                raise CommandError(f"Too many arguments for the '/{self.name}' command.")

    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the model command. This command does not have any subcommands, so this method is left empty.
        """
        pass

