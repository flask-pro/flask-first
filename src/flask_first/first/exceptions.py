"""The module contains the exceptions used in the Flask-First extension."""


class FirstException(Exception):
    """Common exception."""


class FirstOpenAPIValidation(FirstException):
    """Exception for specification validation error."""


class FirstValidation(FirstException):
    """Exception for request validation error."""


class FirstEndpointValidation(FirstValidation):
    """Exception for endpoint validation error."""


class FirstRequestHeadersValidation(FirstValidation):
    """Exception for headers validation error."""


class FirstRequestCookiesValidation(FirstValidation):
    """Exception for cookies validation error."""


class FirstRequestPathArgsValidation(FirstValidation):
    """Exception for path-parameters validation error."""


class FirstRequestArgsValidation(FirstValidation):
    """Exception for request arguments validation error."""


class FirstRequestCookieValidation(FirstValidation):
    """Exception for request cookie validation error."""


class FirstRequestJSONValidation(FirstValidation):
    """Exception for JSON validation error."""


class FirstResponseJSONValidation(FirstValidation):
    """Exception for response validation error."""
