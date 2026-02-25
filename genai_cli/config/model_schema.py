SCHEMA = {
    "type": "object",
    "description": "Schema for defining a model in the GenAI CLI tool.",
    "properties": {
        "models": {
            "type": "object",
            "description": "A dictionary of model configurations.",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "The identifier for the model, used to specify which model to use for generating responses."
                    },
                    "thinking": {
                        "type": "boolean",
                        "description": "Indicates whether the model supports 'thinking' features, which may include advanced reasoning capabilities."
                    }
                },
            "required": ["model_id", "thinking"]
            }
        }
    },
    "required": ["models"]
}

