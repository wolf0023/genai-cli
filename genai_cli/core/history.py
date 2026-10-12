import logging
import os
import json
from uuid import UUID
from jsonschema import validate, ValidationError

from genai_cli.core.session import Session
from genai_cli.const import HISTORY_DIR
from genai_cli.core.history_schema import SCHEMA

class HistoryStorage:
    """ Load and save conversation history to local storage.
    Attributes:
        logger (logging.Logger): Logger for application events and errors.
        history_path (str): The path to store conversation history files.
        sessions (list[Session]): List of conversation data.
    """
    def __init__(self, logger):
        self._logger: logging.Logger = logger

        self._history_path: str = os.path.expanduser(HISTORY_DIR)
        self.sessions: dict[UUID, Session] = {}

        os.makedirs(self._history_path, exist_ok=True)
        self._load_history_files()

    def _load_history_files(self):
        """ Load the list of history files from storage.
        """
        # Clear existing sessions before loading 
        self.sessions.clear()

        # Iterate through files in the history directory and load metadata for valid history files
        loaded: list[Session] = []
        for filename in os.listdir(self._history_path):
            # Skip files that are not valid history files
            if not self._check_valid_file(filename):
                self._logger.error(f"Skipping history file {filename}: invalid file")
                continue

            # Load the list of histories to the sessions
            try:
                with open(os.path.join(self._history_path, filename), "r", encoding="utf-8") as f:
                    history_data = json.load(f)
            except Exception as e:
                self._logger.error(f"Error loading history file {filename}: {str(e)}")
                continue

            # Validate the loaded history data
            try:
                validate(instance=history_data, schema=SCHEMA)
            except ValidationError as e:
                self._logger.error(f"Skipping history file {filename}: invalid format ({e.message})")
                continue

            # Append a history_data to temporary list
            uuid_from_filename: UUID = UUID(filename.removesuffix(".json"))
            loaded.append(Session.create_obj(**history_data, id=uuid_from_filename))

        # Sort by updated date
        for session in sorted(loaded, key=lambda s: s.updated_at):
            self.sessions[session.id] = session

    def _check_valid_file(self, filename: str) -> bool:
        """ Check if a history file is valid.
        Args:
            filename (str): The name of the history file.
        Returns:
            bool: True if the file is valid, False otherwise.
        """
        history_path = os.path.join(self._history_path, filename)

        # Validate file existence and format
        if not os.path.isfile(history_path):
            return False

        # Validate file format
        if not filename.endswith(".json"):
            return False

        # Validate UUID
        try:
            UUID(filename.removesuffix(".json"))
        except ValueError:
            return False

        return True

    def _create_history(self, session_data: Session):
        """ Create a new conversation history file in storage.

        Args:
            session_data (Session): The conversation history data to save.

        Raises:
            Exception: If there is an error creating the history file.
        """
        uuid_str: str = str(session_data.id)
        filename = os.path.basename(f"{uuid_str}.json")
        history_path = os.path.join(self._history_path, filename)

        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=4)
        except Exception as e:
            self._logger.error(f"Error creating history file {filename}: {str(e)}")
            raise Exception(f"Failed to create history file: {str(e)}")

    def save_history(self, session_data: Session):
        """ Save conversation history to storage.
        Overwrite the history file if filename already exists, otherwise create a new file.

        Args:
            session_data (Session): The conversation history data to save.

        Raises:
            Exception: If there is an error saving the history file.
        """
        try: 
            # If the session does not have any messages, skip saving the history file
            if not session_data.messages:
                return

            # If the session is new, create a new history file and append new session to sessions
            if self.sessions.get(session_data.id) is None:
                self._create_history(session_data)
                self.sessions[session_data.id] = session_data
                return

            # Overwrite the existing history file
            history_path = os.path.join(self._history_path, f"{session_data.id}.json")

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=4)
        except Exception as e:
            self._logger.error(f"Error saving history file {session_data.id}.json: {str(e)}")
            raise Exception(f"Failed to save history file: {str(e)}") from e

        # Overwrite the existing session data
        self.sessions[session_data.id] = session_data
