from enum import StrEnum

class Role(StrEnum):
    """ Enumeration of message roles
    """
    DEFAULT = "user"
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
