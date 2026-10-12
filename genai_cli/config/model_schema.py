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
                        "type": ["string", "null"],
                        "enum": ["none", "low", "medium", "high", None],
                        "description": "The thinking level for the model. Set null to disable reasoning_effort for models that do not support it."
                    }
                },
            "required": ["model_id"]
            }
        }
    },
    "required": ["models"]
}
