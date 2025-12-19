from enum import StrEnum

class Role(StrEnum):
    """ Enumeration of message roles
    """
    DEFAULT = "user"
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Provider(StrEnum):
    """ Enumeration of AI model providers
    """
    DEFAULT = "google"
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
