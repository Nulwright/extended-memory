```python
"""Custom Exception Classes for ESM"""

from typing import Optional


class ESMException(Exception):
    """Base exception for ESM application"""
    
    def __init__(
        self, 
        message: str, 
        detail: Optional[str] = None, 
        status_code: int = 500
    ):
        super().__init__(message)
        self.message = message
        self.detail = detail
        self.status_code = status_code
    
    def __str__(self):
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


class ValidationError(ESMException):
    """Raised when validation fails"""
    
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, detail, 400)


class MemoryNotFoundError(ESMException):
    """Raised when a memory cannot be found"""
    
    def __init__(self, memory_id: int):
        super().__init__(
            f"Memory with ID {memory_id} not found",
            detail=f"The requested memory (ID: {memory_id}) does not exist",
            status_code=404
        )
        self.memory_id = memory_id


class AssistantNotFoundError(ESMException):
    """Raised when an assistant cannot be found"""
    
    def __init__(self, assistant_identifier: str):
        super().__init__(
            f"Assistant '{assistant_identifier}' not found",
            detail=f"The requested assistant does not exist",
            status_code=404
        )
        self.assistant_identifier = assistant_identifier


class SearchError(ESMException):
    """Raised when search operations fail"""
    
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Search query: '{query}'" if query else None,
            status_code=500
        )
        self.query = query


class EmbeddingError(ESMException):
    """Raised when embedding generation fails"""
    
    def __init__(self, message: str, text_preview: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Text preview: {text_preview[:100]}..." if text_preview else None,
            status_code=500
        )


class DatabaseError(ESMException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Database operation: {operation}" if operation else None,
            status_code=500
        )
        self.operation = operation


class ExportError(ESMException):
    """Raised when export operations fail"""
    
    def __init__(self, message: str, export_id: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Export ID: {export_id}" if export_id else None,
            status_code=500
        )
        self.export_id = export_id


class ImportError(ESMException):
    """Raised when import operations fail"""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        super().__init__(
            message,
            detail=f"File: {filename}" if filename else None,
            status_code=400
        )
        self.filename = filename


class AuthenticationError(ESMException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class AuthorizationError(ESMException):
    """Raised when authorization fails"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class RateLimitError(ESMException):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ConfigurationError(ESMException):
    """Raised when configuration is invalid"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Configuration key: {config_key}" if config_key else None,
            status_code=500
        )
        self.config_key = config_key


class ServiceUnavailableError(ESMException):
    """Raised when external services are unavailable"""
    
    def __init__(self, service_name: str, message: Optional[str] = None):
        super().__init__(
            message or f"{service_name} service is unavailable",
            detail=f"Service: {service_name}",
            status_code=503
        )
        self.service_name = service_name


class DataIntegrityError(ESMException):
    """Raised when data integrity constraints are violated"""
    
    def __init__(self, message: str, constraint: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Constraint: {constraint}" if constraint else None,
            status_code=422
        )
        self.constraint = constraint


class ResourceLimitError(ESMException):
    """Raised when resource limits are exceeded"""
    
    def __init__(self, resource: str, limit: int, current: int):
        super().__init__(
            f"{resource} limit exceeded",
            detail=f"Limit: {limit}, Current: {current}",
            status_code=413
        )
        self.resource = resource
        self.limit = limit
        self.current = current


class WebSocketError(ESMException):
    """Raised when WebSocket operations fail"""
    
    def __init__(self, message: str, client_id: Optional[str] = None):
        super().__init__(
            message,
            detail=f"Client ID: {client_id}" if client_id else None,
            status_code=500
        )
        self.client_id = client_id

