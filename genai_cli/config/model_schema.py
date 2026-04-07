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
                        "type": "string",
                        "description": "The thinking level for the model, which can be set to 'none', 'low', 'medium', or 'high'. If the model does not support thinking modes, this field will be treated as 'none'."
                    }
                },
            "required": ["model_id"]
            }
        }
    },
    "required": ["models"]
}

