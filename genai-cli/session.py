from dataclasses import dataclass
from datetime import datetime

from enums import Role, Provider

@dataclass
class Message:
    """ Single message in conversation session

    Attributes:
        role (Role): Role of the message sender (e.g., "user", "assistant").
        content (str): Content of the message.
        timestamp (str): Timestamp of when the message was sent.
    """
    role: Role
    content: str
    timestamp: str

@dataclass
class Session:
    """ Conversation session metadata and messages

    Attributes:
        title (str): Title of the conversation.
        provider (Provider): Provider of the AI model.
        created_at (str): Creation timestamp of the conversation.
        updated_at (str): Last updated timestamp of the conversation.
        messages (list[Message]): List of messages in the conversation.
    """
    title: str
    provider: Provider
    created_at: str
    updated_at: str
    messages: list[Message]

    def append_message(
            self,
            role: Role, 
            content: str, 
            timestamp: datetime
    ) -> None:
        """ Append a message to the current conversation session
        Args:
            role (Role): Role of the message sender (e.g. "user", "assistant").
            content (str): Content of the message.
            timestamp (datetime): Timestamp of when the message was sent.
        """
        # Create message
        timestamp_str = timestamp.isoformat(sep=' ', timespec='seconds')
        message = Message(role=role, content=content, timestamp=timestamp_str)

        self.messages.append(message)
        self.updated_at = timestamp_str

    def delete_last_message(self) -> bool:
        """ Delete the last message from the current conversation session
        Returns:
            bool: True if a message was deleted, False if there were no messages.
        """
        # Check if there are messages to delete
        if not self.messages:
            return False

        # Delete the last message
        self.messages.pop()
        self.updated_at = datetime.now().isoformat(sep=' ', timespec='seconds')

        return True


class SessionManager:
    """ Manages conversation session
    Attributes:
        current_session (Session|None): The currently loaded conversation session.
    """
    def __init__(self):
        self.current_session: Session|None = None

    def load_session(
        self,
        title: str,
        provider: Provider,
        created_at: str,
        messages: list[Message]
    ) -> Session:
        """ Load conversation session
        Args:
            title (str): Title of the conversation.
            provider (Provider): Provider of the AI model.
            created_at (str): Creation timestamp of the conversation.
            messages (list[Message]): List of messages in the conversation.
        Returns:
            Session: The created conversation session.
        """
        session = Session(
            title=title,
            provider=provider,
            created_at=created_at,
            updated_at=created_at,
            messages=messages
        )

        # Set current session
        self.current_session = session

        return session

    def create_session(self) -> Session:
        """ Create a new conversation session
        Returns:
            Session: The created conversation session.
        """
        # Get current
        time_now: str = datetime.now().isoformat(' ', timespec='seconds')

        session = Session(
            title="New Conversation",
            provider=Provider.DEFAULT,
            created_at=time_now,
            updated_at=time_now,
            messages=[]
        )
        # Set current session
        self.current_session = session

        return session

    def get_current_session(self) -> Session:
        """ Get the current conversation session
        Returns:
            Session: The current conversation session.
        """
        if self.current_session is None:
            return self.create_session()

        return self.current_session
