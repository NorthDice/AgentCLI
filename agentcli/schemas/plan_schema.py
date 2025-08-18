"""Схема для планов действий."""

# Пример структуры плана
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Исходный запрос на естественном языке"
        },
        "actions": {
            "type": "array",
            "description": "Список действий для выполнения",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Тип действия (read, write, modify, etc.)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу или директории"
                    },
                    "content": {
                        "type": "string",
                        "description": "Содержимое для записи (для write/modify)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Описание действия"
                    }
                },
                "required": ["type", "path", "description"]
            }
        }
    },
    "required": ["query", "actions"]
}


def validate_plan(plan):
    """Валидирует план на соответствие схеме.
    
    Args:
        plan (dict): План для валидации.
        
    Returns:
        bool: Соответствует ли план схеме.
    """
    # TODO: Реализовать проверку плана на соответствие схеме
    return True
