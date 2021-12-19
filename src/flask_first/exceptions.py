"""The module contains the exceptions used in the Flask-First extension."""
from flask import current_app
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import Response


def _bad_request(description: str) -> Response:
    return make_response(jsonify(code=400, name='Bad Request', description=description), 400)


class FirstException(Exception):
    """Common exception."""


class FirstOpenAPIValidation(FirstException):
    """Exception for specification validation error."""


class FirstValidation(FirstException):
    """Exception for request validation error."""


class FirstRequestPathParamValidation(FirstValidation):
    """Exception for path-parameters validation error."""


class FirstRequestArgsValidation(FirstValidation):
    """Exception for path-parameters validation error."""


class FirstRequestJSONValidation(FirstValidation):
    """Exception for JSON validation error."""


class FirstResponseJSONValidation(FirstValidation):
    """Exception for response validation error."""


def register_errors(app: Flask) -> None:
    """Registering handlers for common errors."""

    @app.errorhandler(FirstRequestPathParamValidation)
    def path_parameter_validation_exception(exc) -> Response:
        current_app.logger.debug(exc)
        return _bad_request(str(exc))

    @app.errorhandler(FirstRequestArgsValidation)
    def args_validation_exception(exc) -> Response:
        current_app.logger.debug(exc)
        return _bad_request(str(exc))

    @app.errorhandler(FirstRequestJSONValidation)
    def json_validation_exception(exc) -> Response:
        current_app.logger.debug(exc)
        return _bad_request(str(exc))

    @app.errorhandler(FirstResponseJSONValidation)
    def response_validation_exception(exc) -> Response:
        current_app.logger.error(exc)
        return make_response(
            jsonify(code=500, name='Internal Server Error', description=str(exc)), 500
        )
