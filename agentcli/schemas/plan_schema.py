"""Schema for action plans."""

# Example plan structure
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Original natural language query"
        },
        "actions": {
            "type": "array",
            "description": "List of actions to execute",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Action type (read, write, modify, etc.)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write (for write/modify actions)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the action"
                    }
                },
                "required": ["type", "path", "description"]
            }
        }
    },
    "required": ["query", "actions"]
}


def validate_plan(plan):
    """Validates a plan against the schema.
    
    Args:
        plan (dict): Plan to validate.
        
    Returns:
        bool: Whether the plan conforms to the schema.
    """
    # TODO: Implement plan validation against the schema
    return True
