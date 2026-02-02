import os
import json
from datetime import datetime

from core.session import Session
from const import HISTORY_DIR

class HistoryStorage:
    """ Load and save conversation history to local storage.
    Attributes:
        history_path (str): The path to store conversation history files.
    """
    def __init__(self):
        self.history_path = os.path.expanduser(HISTORY_DIR)
        self.history_files: list[str] = []

        os.makedirs(self.history_path, exist_ok=True)
        self._load_history_files()

    def _load_history_files(self):
        """ Load the list of history files from storage.
        """
        self.history_files = [
            file for file in os.listdir(self.history_path)
            if os.path.isfile(os.path.join(self.history_path, file)) and file.endswith(".json")
        ]

    def get_filename(self, num: int) -> str:
        """ Get the filename of a history file by index.
        Args:
            num (int): The index of the history file.
        Returns:
            str: The filename of the history file.
        """
        if num < 0 or num >= len(self.history_files):
            raise IndexError("History file index out of range.")

        return self.history_files[num]

    def _check_valid_file(self, filename: str) -> bool:
        """ Check if a history file is valid.
        Args:
            filename (str): The name of the history file.
        Returns:
            bool: True if the file is valid, False otherwise.
        """
        history_path = os.path.join(self.history_path, filename)

        # Validate file existence and format
        if not os.path.isfile(history_path):
            return False

        # Validate file format
        if not filename.endswith(".json"):
            return False

        return True

    def _get_title(self, num: int ) -> str:
        """ Get the titles of all stored conversation histories.
        Args:
            num (int): The index of the history file to get the title from.
        Returns:
            str: The title of the conversation history.
        """
        # Check index validity
        if num < 0 or num >= len(self.history_files):
            raise IndexError("History file index out of range.")

        filename = self.get_filename(num)
        history_path = os.path.join(self.history_path, filename)

        if not self._check_valid_file(filename):
            raise Exception(f"Invalid history file: {filename}")

        # Load title from history file
        with open(history_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("title")

    def get_history_titles(self) -> list[str]:
        """ Get the titles of all stored conversation histories.
        Returns:
            list[str]: List of conversation history titles.
        """
        titles: list[str] = []
        for index, _ in enumerate(self.history_files):
            try:
                title = self._get_title(index)
                titles.append(title)
            except (Exception):
                # Skip files that cannot be read or parsed
                continue

        return titles

    def get_history(self, filename: str) -> Session:
        """ Load conversation history from storage.
        Args:
            filename (str): The name of the history file to load.
        Returns:
            Session: The loaded conversation history data.
        """
        history_data: dict = {}

        if not self._check_valid_file(filename):
            raise Exception(f"Invalid history file: {filename}")

        history_path = os.path.join(self.history_path, filename)
        with open(history_path, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        return Session.create_obj(**history_data)

    def save_history(
        self,
        session_data: Session,
    ):
        """ Save conversation history to storage.
        Delete old file and create a new one.
        Args:
            history_data (dict[str, str|list[dict[str, str]]]): The conversation history data to save.
            filename (str|None): The name of the history file to replace. If None, a new file is created.
            timestamp (datetime): The timestamp to use for the filename.
        """
        # Create as new file
        timestamp = datetime.fromisoformat(session_data.created_at)
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        new_filename = f"history_{timestamp_str}.json"
        new_history_path = os.path.join(self.history_path, new_filename)

        with open(new_history_path, "w", encoding="utf-8") as f:
            json.dump(session_data.to_dict(), f, ensure_ascii=False, indent=4)

        # If num is None, just save as new file
        if session_data.filename is None:
            self._load_history_files()
            return

        # Check file validity
        if not self._check_valid_file(session_data.filename):
            raise Exception(f"History file not found: {session_data.filename}")

        # Delete old file
        history_path = os.path.join(self.history_path, session_data.filename)
        os.remove(history_path)

        # Reload history files
        self._load_history_files()

