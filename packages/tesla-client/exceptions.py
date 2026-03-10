"""
Tesla Fleet API Exceptions

Custom exceptions for Tesla API errors.
"""


class TeslaAPIError(Exception):
    """Base exception for Tesla API errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(TeslaAPIError):
    """Raised when authentication fails."""
    pass


class VehicleUnavailableError(TeslaAPIError):
    """Raised when vehicle is offline or unavailable."""
    pass


class RateLimitError(TeslaAPIError):
    """Raised when API rate limit is exceeded."""
    pass


class CommandFailedError(TeslaAPIError):
    """Raised when a vehicle command fails."""
    pass


class InvalidParameterError(TeslaAPIError):
    """Raised when invalid parameters are provided."""
    pass


class ServerError(TeslaAPIError):
    """Raised when Tesla server returns 5xx error."""
    pass
