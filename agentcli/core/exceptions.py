"""Custom exceptions for AgentCLI."""


class AgentCLIError(Exception):
    """Base class for all AgentCLI exceptions."""
    pass


class PlanError(AgentCLIError):
    """Error during plan creation or loading."""
    pass


class ExecutionError(AgentCLIError):
    """Error while executing a plan."""
    pass


class ActionError(AgentCLIError):
    """Error while executing a specific action."""
    
    def __init__(self, message, action=None, cause=None):
        """Initialize the exception.
        
        Args:
            message (str): Error message
            action (dict, optional): Action that caused the error
            cause (Exception, optional): Underlying exception that caused the error
        """
        self.action = action
        self.cause = cause
        super().__init__(message)


class RollbackError(AgentCLIError):
    """Error during rollback of changes."""
    pass


class ValidationError(AgentCLIError):
    """Validation error in a plan or action."""
    pass


class FileOperationError(AgentCLIError):
    """Error during file operations."""
    
    def __init__(self, message, file_path=None, operation=None, cause=None):
        """Initialize the exception.
        
        Args:
            message (str): Error message
            file_path (str, optional): Path to the file
            operation (str, optional): Operation type (read, write, delete)
            cause (Exception, optional): Underlying exception that caused the error
        """
        self.file_path = file_path
        self.operation = operation
        self.cause = cause
        super().__init__(message)


class LLMServiceError(AgentCLIError):
    """Error while interacting with the LLM service."""
    pass
