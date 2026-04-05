class MidtransError(Exception):
    """Base exception for Midtrans errors."""

    def __init__(self, message="", status_code=None, data=None):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(self.message)


class MidtransAPIError(MidtransError):
    """General API error."""
    pass


class MidtransAuthenticationError(MidtransError):
    """Authentication failed (401)."""

    def __init__(self, message="Authentication failed"):
        super().__init__(message, status_code=401)


class MidtransValidationError(MidtransError):
    """Validation error (400)."""

    def __init__(self, message="Validation error", data=None):
        super().__init__(message, status_code=400, data=data)


class MidtransDuplicateOrderError(MidtransError):
    """Duplicate order ID (406)."""

    def __init__(self, message="Duplicate order ID"):
        super().__init__(message, status_code=406)


class MidtransRateLimitError(MidtransError):
    """Rate limit exceeded (429)."""

    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, status_code=429)


class MidtransSignatureError(MidtransError):
    """Invalid notification signature."""

    def __init__(self, message="Invalid signature"):
        super().__init__(message, status_code=403)
