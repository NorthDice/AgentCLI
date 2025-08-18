"""Пользовательские исключения для AgentCLI."""


class AgentCLIError(Exception):
    """Базовый класс для всех исключений AgentCLI."""
    pass


class PlanError(AgentCLIError):
    """Ошибка при создании или загрузке плана."""
    pass


class ExecutionError(AgentCLIError):
    """Ошибка при выполнении плана."""
    pass


class ActionError(AgentCLIError):
    """Ошибка при выполнении конкретного действия."""
    
    def __init__(self, message, action=None, cause=None):
        """Инициализация исключения.
        
        Args:
            message (str): Сообщение об ошибке
            action (dict, optional): Действие, которое вызвало ошибку
            cause (Exception, optional): Исключение, которое вызвало ошибку
        """
        self.action = action
        self.cause = cause
        super().__init__(message)


class RollbackError(AgentCLIError):
    """Ошибка при откате изменений."""
    pass


class ValidationError(AgentCLIError):
    """Ошибка валидации плана или действия."""
    pass


class FileOperationError(AgentCLIError):
    """Ошибка при операциях с файлами."""
    
    def __init__(self, message, file_path=None, operation=None, cause=None):
        """Инициализация исключения.
        
        Args:
            message (str): Сообщение об ошибке
            file_path (str, optional): Путь к файлу
            operation (str, optional): Тип операции (read, write, delete)
            cause (Exception, optional): Исключение, которое вызвало ошибку
        """
        self.file_path = file_path
        self.operation = operation
        self.cause = cause
        super().__init__(message)


class LLMServiceError(AgentCLIError):
    """Ошибка при взаимодействии с LLM сервисом."""
    pass
