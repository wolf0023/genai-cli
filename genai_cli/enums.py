from enum import StrEnum

class Role(StrEnum):
    """ Enumeration of message roles
    """
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
