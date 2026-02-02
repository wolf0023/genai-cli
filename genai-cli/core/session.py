from dataclasses import dataclass
from datetime import datetime

from enums import Role

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

    @classmethod
    def create_obj(
        cls,
        role: str,
        content: str,
        timestamp:str
    ) -> 'Message':
        """ Create a Message instance from given parameters
        Args:
            role (str): Role of the message sender (e.g. "user", "assistant").
            content (str): Content of the message.
            timestamp (str): Timestamp of when the message was sent.
        Returns:
            Message: The created Message instance.
        """
        return cls(
            role=Role(role),
            content=content,
            timestamp=timestamp
        )

    def to_dict(self) -> dict[str, str]:
        """ Convert the message to a dictionary format
        Returns:
            dict[str, str]: Dictionary format of the message including timestamp.
        """
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp
        }

@dataclass
class Session:
    """ Conversation session metadata and messages

    Attributes:
        title (str): Title of the conversation.
        model (str): AI model used in the conversation.
        created_at (str): Creation timestamp of the conversation.
        updated_at (str): Last updated timestamp of the conversation.
        messages (list[Message]): List of messages in the conversation.
        filename (str|None): Optional filename that is associated with the session.
    """
    title: str
    model: str
    created_at: str
    updated_at: str
    messages: list[Message]
    filename: str|None = None

    @classmethod
    def create_obj(
        cls,
        title: str,
        model: str,
        created_at: str,
        updated_at: str,
        messages: list[dict[str, str]],
        filename: str|None = None
    ) -> 'Session':
        """ Create a Session instance from given parameters
        Args:
            title (str): Title of the conversation.
            model (str): AI model used in the conversation.
            created_at (str): Creation timestamp of the conversation.
            updated_at (str): Last updated timestamp of the conversation.
            messages (list[dict[str, str]]): List of messages in the conversation.
            filename (str|None): Optional filename that is associated with the session.
        Returns:
            Session: The created Session instance.
        """
        # Create message objects
        message_objects = [Message.create_obj(**msg) for msg in messages]

        return cls(
            title=title,
            model=model,
            created_at=created_at,
            updated_at=updated_at,
            messages=message_objects,
            filename=filename
        )

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

    def to_dict(self) -> dict[str, str|list[dict[str, str]]]:
        """ Convert the session to a dictionary format
        Returns:
            dict[str, str|list[dict[str, str]]]: Dictionary representation of the session.
        """
        return {
            "title": self.title,
            "model": self.model,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [
                message.to_dict()
                for message in self.messages
            ]
        }

class SessionManager:
    """ Manages conversation session
    Attributes:
        current_session (Session|None): The currently loaded conversation session.
    """
    def __init__(self):
        self.current_session: Session|None = None

    def load_session(
        self,
        history_data: Session
    ) -> None:
        """ Load conversation session
        Args:
            history_data (Session): The conversation session data to load.
        """
        # Set current session
        self.current_session = history_data

    def create_session(
            self,
            title: str = "New Conversation"
    ) -> Session:
        """ Create a new conversation session
        Args:
            title (str): Title of the new conversation session.
        Returns:
            Session: The created conversation session.
        """
        # Get current
        time_now: str = datetime.now().isoformat(' ', timespec='seconds')

        session = Session(
            title=title,
            model="gemini_flash",
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
        Raises:
            ValueError: If no session is currently loaded.
        """
        if self.current_session is None:
            raise ValueError("No session is currently loaded.")

        return self.current_session

    def clear_session(self) -> None:
        """ Clear the current conversation session
        Note:
            This does not delete the session from storage; it only clears the in-memory reference.
        """
        self.current_session = None

