SCHEMA = {
    "type": "object",
    "description": "History schema for the GenAI CLI tool.",
    "properties": {
        "title": {
            "type": "string",
            "description": "Title of the conversation."
        },
        "model": {
            "type": "string",
            "description": "The AI model to use for the conversation session."
        },
        "created_at": {
            "type": "string",
            "description": "Creation timestamp of the conversation."
        },
        "updated_at": {
            "type": "string",
            "description": "Last updated timestamp of the conversation."
        },
        "messages": {
            "type": "array",
            "description": "List of messages in the conversation.",
            "items": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "Role of the message sender (e.g., \"user\", \"assistant\")."
                    },
                    "content": {
                        "type": "string",
                        "description": "Content of the message."
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "Timestamp of when the message was sent."
                    },
                },
                "required": ["role", "content", "timestamp"]
            },
        }
    },
    "required": ["title", "model", "created_at", "updated_at", "messages"]
}

