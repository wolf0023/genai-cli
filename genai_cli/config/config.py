from dataclasses import dataclass, asdict
import os
import json
from jsonschema import validate, ValidationError
import logging

from genai_cli.const import CONFIG_DIR, CONFIG_FILE
from genai_cli.config.config_schema import SCHEMA

@dataclass
class Config:
    """ Configuration for genai-cli

    Attributes:
        default_model (str): The default model to use for chat interactions.
        system_prompt (str): The system prompt to use for chat interactions.
        history_len (int): The number of past messages to include in the chat history.
        start_with_last_session (bool): Whether to start with the last session when launching the app.
        your_name (str): The name to use for the user in chat interactions.
    """
    default_model: str = "gemini_pro"
    system_prompt: str = "you are a helpful AI assistant."
    history_len: int = 100
    start_with_last_session: bool = True
    your_name: str = "user"

class ConfigManager:
    """ Load and manage configuration settings.

    Attributes:
        config (Config): The loaded configuration settings.
        config_path (str): The path to the configuration directory.
        config_file (str): The path to the configuration file.
        config_schema (str): The path to the configuration schema file.
        logger (logging.Logger): Logger instance for logging messages.

    Raises:
        Exception: If there is an error loading the config file, an exception will be raised.
    """
    def __init__(self, logger: logging.Logger):
        self.config: Config = Config()
        self.config_path: str = os.path.expanduser(CONFIG_DIR)
        self.config_file: str = os.path.join(self.config_path, CONFIG_FILE)
        self.config_schema: str = os.path.join(os.path.dirname(__file__), 'config_schema.json')
        self.logger = logger

        os.makedirs(self.config_path, exist_ok=True)

    def _create_config_file(self):
        """ Create a new configuration file with default settings.

        Note:
            This will overwrite any existing configuration file, so use with caution.

        Raises:
            Exception: If there is an error creating the config file, an exception will be raised.
        """
        try:
            default_config = asdict(Config())
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)

        except Exception as e:
            self.logger.error(f"Failed to create config file: {e}")
            raise

    def load_config(self):
        """ Load configuration settings from file.

        Raises:
            ValidationError: If the loaded config does not conform to the schema, a ValidationError will be raised.
            Exception: If there is an error loading the config file, an exception will be raised.
        """
        # if config file does not exist, copy the default one
        if not os.path.isfile(self.config_file):
            self._create_config_file()

        try:
            # Load config from the configuration file
            with open(self.config_file, 'r') as f:
                configs = json.load(f)

            # Validate the loaded config
            validate(instance=configs, schema=SCHEMA)

            # Overwrite Config object from loaded settings
            self.config = Config(**configs)

        except ValidationError as e:
            self.logger.error(f"Config validation error: {e.message}")
            raise

        except Exception as e:
            self.logger.error(f"Failed to load config file: {e}")
            raise
