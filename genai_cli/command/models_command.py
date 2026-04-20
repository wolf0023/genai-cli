from typing_extensions import override

from genai_cli.command.base import BaseCommand
from genai_cli.command.base import CommandError
from genai_cli.config.model import Model

class ModelsCommand(BaseCommand):
    """Command to list available models
    """
    name = "models"
    description = "Display all available models"
    usage = "/models"

    def __init__(
        self,
        models: list[Model]
    ):
        super().__init__()
        self.models: list[Model] = models

    def _list_models(self) -> list[str]:
        return [
            f"[command-list]* [/command-list][command-output]{model.model_name} ({model.model_id})[/command-output]"
            for model in self.models
        ]

    @override
    def execute(self, argc: int, argv: list[str]) -> str:
        """Execute the models commands to display all available models
        """
        match argc:
            case 1:
                if not self.models:
                    raise CommandError("No available models found. To start a chat, you must define the models in the model configuration file.")

                formats: list[str] = self._list_models()
                formats.insert(0, "[command-header]Available models:[/command-header]")

                return "\n".join(formats)

            case _:
                raise CommandError(f"The '/{self.name}' command does not take any arguments.")

    @override
    def _register_all_subcommands(self):
        """Register all subcommands for the models command. This command does not have any subcommands, so this method is left empty.
        """
        pass

    @override
    def get_options(self) -> list[str]:
        """This command does not have any options, so this method returns an empty set.

        Returns:
            list[str]: An empty set, as the models command does not have any options.
        """
        return []
