from dataclasses import dataclass
import os
import json
import shutil

from const import CONFIG_DIR, MODELS_FILE

@dataclass
class Model:
    """ Single model configuration.
    Attributes:
        model_name (str): Name of the model.
        model_id (str): Identifier of the model.
        thinking (bool): Whether use thinking mode. (if applicable)
    """
    model_name: str
    model_id: str
    thinking: bool = False

class ModelConfig:
    """ Load models configuration.
    Attributes:
        model_path (str): The path to the models configuration directory.
        models_file (str): The path to the models configuration file.
        default_file (str): The path to the default models configuration file.
        models (list[Model]): List of loaded model configurations.
    """
    def __init__(self):
        self.models_path: str = os.path.expanduser(CONFIG_DIR)
        self.models_file: str = os.path.join(self.models_path, MODELS_FILE)
        self.default_file: str = os.path.join(os.path.dirname(__file__), MODELS_FILE)
        self.models: list[Model] = []

        os.makedirs(self.models_path, exist_ok=True)

    def get_model(self, model_name: str) -> Model | None:
        """ Get a model configuration by name.
        Args:
            model_name (str): The name of the model to retrieve.
        Returns:
            Model | None: The model configuration if found, None otherwise.
        """
        for model in self.models:
            if model.model_name == model_name:
                return model
        return None

    def load_models(self):
        """ Load models from the configuration file."
        """
        # If models file does not exist, copy the default one
        if not os.path.isfile(self.models_file):
            shutil.copyfile(self.default_file, self.models_file)

        # Load models from the configuration file
        with open(self.models_file, "r", encoding="utf-8") as f:
            models_data = json.load(f)

        # Parse models data
        self.models = [
            Model(
                model_name=name,
                model_id=model["model_id"],
                thinking=model["thinking"]
            )
            for name, model in models_data["models"].items()
        ]

    def get_model_names(self) -> list[str]:
        """ Get the list of model names.
        Returns:
            list[str]: List of model names.
        """
        return [model.model_name for model in self.models]
