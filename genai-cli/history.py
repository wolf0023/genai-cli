from typing import List
from dataclasses import dataclass
from datetime import datetime, time

from enums import Role, Provider

@dataclass
class Message:
    """ Single message in conversation history

    Attributes:
        role (str): Role of the message sender (e.g., "user", "model").
        content (str): Content of the message.
        timestamp (str): Timestamp of when the message was sent.
    """
    role: Role
    content: str
    timestamp: str

@dataclass
class History:
    """ Conversation history metadata and messages

    Attributes:
        title (str): Title of the conversation.
        provider (str): Provider of the AI model.
        created_at (str): Creation timestamp of the conversation.
        updated_at (str): Last updated timestamp of the conversation.
        messages (List[Message]): List of messages in the conversation.
    """
    title: str
    provider: Provider
    created_at: str
    updated_at: str
    messages: List[Message]

class HistoryManager:
    """ Manages conversation histories
    Attributes:
        current_history (History|None): The currently loaded conversation history.
    """
    def __init__(self):
        self.current_history: History|None = None

    def load_history(
        self,
        title: str,
        provider: str,
        created_at: str,
        messages: list
    ) -> History:
        """ Load conversation history
        Args:
            title (str): Title of the conversation.
            provider (str): Provider of the AI model.
            created_at (str): Creation timestamp of the conversation.
            messages (List[Message]): List of messages in the conversation.
        Returns:
            History: The created conversation history.
        """
        # Convert message dicts to Message objects
        message_objs = [Message(**msg) for msg in messages]

        # Convert provider string to Provider enum
        try:
            provider = Provider(provider)
        except ValueError:
            provider = Provider.DEFAULT

        history = History(
            title=title,
            provider=provider,
            created_at=created_at,
            updated_at=created_at,
            messages=message_objs
        )
        self.current_history = history
        return history

    def create_history(self) -> History:
        """ Create a new conversation history
        Returns:
            History: The created conversation history.
        """
        history = History(
            title="New Conversation",
            provider=Provider.DEFAULT,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            messages=[]
        )
        self.current_history = history
        return history

    def append_message(
            self,
            _role: str, 
            _content: str, 
            _timestamp: datetime
    ) -> None:
        """ Append a message to the current conversation history
        Args:
            role (str): Role of the message sender (e.g. "user", "model").
            content (str): Content of the message.
            timestamp (str): Timestamp of when the message was sent.
        """
        # Check if history is loaded
        if self.current_history is None:
            self.create_history()

        try:
            role: Role = Role(_role)
        except ValueError:
            role: Role = Role.DEFAULT

        # Create message
        timestamp = _timestamp.isoformat(sep=' ', timespec='seconds')
        message = Message(role=role, content=_content, timestamp=timestamp)

        self.current_history.messages.append(message)
        self.current_history.updated_at = timestamp

    def delete_last_message(self) -> None:
        """ Delete the last message from the current conversation history
        """
        # Check if history is loaded
        if self.current_history is None:
            raise ValueError("No conversation history loaded.")

        if not self.current_history.messages:
            raise ValueError("No messages to delete.")

        self.current_history.messages.pop()

