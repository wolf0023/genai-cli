from dataclasses import dataclass
import os
import json
import shutil
from jsonschema import validate, ValidationError

from const import CONFIG_DIR, MODELS_FILE
from config.model_schema import SCHEMA

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
        config_path (str): The path to the models configuration directory.
        models_file (str): The path to the models configuration file.
        default_file (str): The path to the default models configuration file.
        models (list[Model]): List of loaded model configurations.
    """
    def __init__(self):
        self.config_path: str = os.path.expanduser(CONFIG_DIR)
        self.models_file: str = os.path.join(self.config_path, MODELS_FILE)
        self.default_file: str = os.path.join(os.path.dirname(__file__), MODELS_FILE)
        self.models: list[Model] = []

        os.makedirs(self.config_path, exist_ok=True)

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

        Raises:
            ValueError: If the loaded models configuration is empty or invalid, a ValueError will be raised.
            ValidationError: If the loaded models configuration does not conform to the schema, a ValidationError will be raised.
        """
        # If models file does not exist, copy the default one
        if not os.path.isfile(self.models_file):
            shutil.copyfile(self.default_file, self.models_file)

        # Load models from the configuration file
        with open(self.models_file, "r", encoding="utf-8") as f:
            models_data = json.load(f)

        # Check if the loaded data is empty
        if not models_data or models_data.get("models") is None:
            raise ValueError("Models configuration is empty. Please check the models configuration file.")

        # Validate the loaded models data
        try:
            validate(instance=models_data, schema=SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Invalid models configuration: {e.message}")

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
