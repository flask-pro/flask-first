"""The module contains the exceptions used in the Flask-First extension."""


class FirstException(Exception):
    """Common exception."""


class FirstRequestValidationError(FirstException):
    """Request validation errors exception."""


class FirstResponseValidationError(FirstException):
    """Response validation errors exception."""
