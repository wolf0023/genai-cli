import logging
import os
import json
from datetime import datetime
from dataclasses import dataclass

from genai_cli.core.session import Session
from genai_cli.const import HISTORY_DIR

@dataclass
class History:
    """ Conversation history metadata and messages
    Attributes:
        title (str): Title of the conversation.
        filename (str): The filename associated with the conversation history.
    """
    title: str
    filename: str

class HistoryStorage:
    """ Load and save conversation history to local storage.
    Attributes:
        logger (logging.Logger): Logger for application events and errors.
        history_path (str): The path to store conversation history files.
        histories (list[History]): List of conversation history metadata.
    """
    def __init__(self, logger):
        self._logger: logging.Logger = logger

        self._history_path: str = os.path.expanduser(HISTORY_DIR)
        self.histories: list[History] = []

        os.makedirs(self._history_path, exist_ok=True)
        self._load_history_files()

    def _load_history_files(self):
        """ Load the list of history files from storage.
        """
        # Clear existing history metadata list before loading
        self.histories.clear()

        # Iterate through files in the history directory and load metadata for valid history files
        for filename in sorted(os.listdir(self._history_path), reverse=True):
            # Skip files that are not valid history files
            if not self._check_valid_file(filename):
                continue

            # Read the title from the history file
            try:
                with open(os.path.join(self._history_path, filename), "r", encoding="utf-8") as f:
                    history_data = json.load(f)
            except Exception as e:
                self._logger.error(f"Error loading history file {filename}: {str(e)}")
                continue

            title = history_data.get("title", "Untitled Conversation")
            self.histories.append(History(title=title, filename=filename))

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

        return True

    def _create_history(self, session_data: Session):
        """ Create a new conversation history file in storage.

        Args:
            session_data (Session): The conversation history data to save.

        Raises:
            Exception: If there is an error creating the history file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{timestamp}.json"
        history_path = os.path.join(self._history_path, filename)

        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=4)
        except Exception as e:
            self._logger.error(f"Error creating history file {filename}: {str(e)}")
            raise Exception(f"Failed to create history file: {str(e)}")

        # Update history files list after creating a new history file
        self._load_history_files()

    def get_history(self, filename: str) -> Session:
        """ Load conversation history from storage.

        Args:
            filename (str): The name of the history file to load.

        Returns:
            Session: The loaded conversation history data.

        Raises:
            Exception: If the history file is invalid or cannot be loaded.
        """
        history_data: dict = {}

        if not self._check_valid_file(filename):
            raise Exception(f"Invalid history file: {filename}")

        history_path = os.path.join(self._history_path, filename)

        try:
            with open(history_path, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception as e:
            self._logger.error(f"Error loading history file {filename}: {str(e)}")
            raise Exception(f"Failed to load history file: {str(e)}")

        return Session.create_obj(**history_data, filename=filename)

    def save_history(self, session_data: Session):
        """ Save conversation history to storage.
        Overwrite the history file if filename already exists, otherwise create a new file with a timestamp.

        Args:
            history_data (dict[str, str|list[dict[str, str]]]): The conversation history data to save.
            filename (str|None): The name of the history file to replace. If None, a new file is created.

        Raises:
            Exception: If there is an error saving the history file.
        """
        try: 
            # If the session does not have any messages, skip saving the history file
            if not session_data.messages:
                return

            # If the session is new, create a new history file with a timestamp
            if session_data.filename is None or not self._check_valid_file(session_data.filename):
                self._create_history(session_data)
                return

            # If the session has an existing filename, overwrite the existing history file
            history_path = os.path.join(self._history_path, session_data.filename)

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=4)
        except Exception as e:
            self._logger.error(f"Error saving history file {session_data.filename}: {str(e)}")
            raise Exception(f"Failed to save history file: {str(e)}")

        # Update history files list after saving the history file
        self._load_history_files()
