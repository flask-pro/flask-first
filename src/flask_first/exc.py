"""The module contains the exceptions used in the Flask-First extension."""
from flask import current_app
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import Response


class FlaskFirstException(Exception):
    """Common exception."""


class FlaskFirstSpecificationValidation(FlaskFirstException):
    """Exception for specification validation error."""


class FlaskFirstValidation(FlaskFirstException):
    """Exception for request validation error."""


class FlaskFirstPathParameterValidation(FlaskFirstValidation):
    """Exception for path-parameters validation error."""


class FlaskFirstArgsValidation(FlaskFirstValidation):
    """Exception for path-parameters validation error."""


class FlaskFirstJSONValidation(FlaskFirstValidation):
    """Exception for JSON validation error."""


class FlaskFirstRequestValidation(FlaskFirstValidation):
    """Exception for request validation error."""


class FlaskFirstResponseValidation(FlaskFirstValidation):
    """Exception for response validation error."""


def register_errors(app: Flask) -> None:
    """Registering handlers for common errors."""

    @app.errorhandler(FlaskFirstPathParameterValidation)
    def path_parameter_validation_exception(exc) -> Response:
        current_app.logger.debug(exc)
        return make_response(jsonify(code=400, name='Bad Request', description=str(exc)), 400)

    @app.errorhandler(FlaskFirstArgsValidation)
    def args_validation_exception(exc) -> Response:
        current_app.logger.debug(exc)
        return make_response(jsonify(code=400, name='Bad Request', description=str(exc)), 400)

    @app.errorhandler(FlaskFirstJSONValidation)
    def json_validation_exception(exc) -> Response:
        current_app.logger.debug(exc)
        return make_response(jsonify(code=400, name='Bad Request', description=str(exc)), 400)

    @app.errorhandler(FlaskFirstResponseValidation)
    def response_validation_exception(exc) -> Response:
        current_app.logger.error(exc)
        return make_response(
            jsonify(code=500, name='Internal Server Error', description=str(exc)), 500
        )
