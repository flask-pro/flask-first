"""Flask extension for using “specification first” principle."""
from flask import Flask
from flask import Request
from flask import request
from flask import Response
from werkzeug.datastructures import MultiDict

from .exc import FlaskFirstArgsValidation
from .exc import FlaskFirstException
from .exc import FlaskFirstJSONValidation
from .exc import FlaskFirstPathParameterValidation
from .exc import FlaskFirstResponseValidation
from .exc import FlaskFirstValidation
from .exc import register_errors
from .spec_parser import Specification
from .validators import validate_json
from .validators import validate_params

__version__ = '0.5.0'


class First:
    """This class is used to generation routes from OpenAPI specification."""

    def __init__(self, path_to_spec: str, app: Flask = None) -> None:
        self.app = app
        self.path_to_spec = path_to_spec

        if self.app is not None:
            self.init_app(app)

        self.spec = Specification(path_to_spec)

        self._mapped_routes_from_spec = []

    @staticmethod
    def route_to_openapi_format(route: str) -> str:
        return route.replace('<', '{').replace('>', '}').replace('int:', '').replace('float:', '')

    def _route_registration_in_flask(self, func: callable) -> None:
        route = None
        route_method = None

        for path, path_item in self.spec.serialized['paths'].items():
            for method, operation in path_item.items():
                if method == 'parameters':
                    continue
                if operation.get('operationId') == func.__name__:
                    route: str = path
                    route_method: str = method

        if not route:
            raise FlaskFirstException(
                f'Route function <{route}> not found in OpenAPI specification!'
            )

        parameters_schemas = self._extract_params_schemas(method, route)
        parameters_for_rule = {}
        for parameter, schema in parameters_schemas.items():
            if schema['in_'] == 'path':
                parameters_for_rule.update(
                    {parameter: f'<{schema["schema"]["type_"]}:{parameter}>'}
                )

        flask_format_rule = route.format(**parameters_for_rule)
        flask_format_rule = (
            flask_format_rule.replace('string:', '')
            .replace('integer:', 'int:')
            .replace('number:', 'float:')
        )
        self.app.add_url_rule(
            flask_format_rule, func.__name__, func, methods=[route_method.upper()]
        )

        self._mapped_routes_from_spec.append(flask_format_rule)

    def _extract_data_from_request(self, request: Request) -> tuple:
        method = request.method.lower()

        if request.url_rule is not None:
            route = request.url_rule.rule
        else:
            route = request.url_rule

        path_parameters = request.view_args
        args = request.args
        json = request.json
        return method, route, path_parameters, args, json

    def _extract_params_schemas(self, method: str, route: str) -> dict:
        parameters = {}

        try:
            if self.spec.serialized['paths'][route].get('parameters'):
                parameters.update(self.spec.serialized['paths'][route]['parameters'])
        except KeyError:
            raise FlaskFirstException(f'Route <{request.endpoint}> not found in specification!')

        try:
            if self.spec.serialized['paths'][route][method].get('parameters'):
                parameters.update(self.spec.serialized['paths'][route][method]['parameters'])
        except KeyError:
            raise FlaskFirstException(f'Method <{method}> not found in route <{request.endpoint}>!')

        return parameters

    def _args_to_dict(self, args: MultiDict) -> dict:
        rendered_args = {}
        for key, value in args.to_dict(flat=False).items():
            if len(value) == 1:
                rendered_args[key] = value[0]
            if len(value) > 1:
                rendered_args[key] = value
        return rendered_args

    def _register_before_request_validation(self) -> None:
        @self.app.before_request
        def add_request_validating() -> None:
            method, route, path_params, args, json = self._extract_data_from_request(request)

            if route not in self._mapped_routes_from_spec:
                return

            route_as_in_spec = self.route_to_openapi_format(route)
            params_from_schema = self._extract_params_schemas(method, route_as_in_spec)

            if path_params:
                try:
                    request.first_view_args = validate_params(path_params, params_from_schema)
                except FlaskFirstValidation as e:
                    raise FlaskFirstPathParameterValidation(e)

            if args:
                try:
                    request.first_args = validate_params(
                        self._args_to_dict(args), params_from_schema
                    )
                except FlaskFirstValidation as e:
                    raise FlaskFirstArgsValidation(e)

            if json:
                json_request_schema = self.spec.serialized['paths'][route_as_in_spec][method][
                    'requestBody'
                ]['content'][request.content_type]['schema']
                try:
                    request.first_json = validate_json(request.json, json_request_schema)
                except FlaskFirstValidation as e:
                    raise FlaskFirstJSONValidation(str(e))

    def _register_after_request_validation(self) -> None:
        @self.app.after_request
        def add_response_validating(response: Response) -> Response:
            method, route, _, _, _ = self._extract_data_from_request(request)

            if route not in self._mapped_routes_from_spec:
                return response

            route_as_in_spec = self.route_to_openapi_format(route)
            schema = self.spec.serialized['paths'][route_as_in_spec][method]['responses'][
                str(response.status_code)
            ]['content'][response.content_type]['schema']

            try:
                validate_json(response.json, schema)
                return response
            except FlaskFirstValidation as e:
                raise FlaskFirstResponseValidation(e)

    def init_app(self, app: Flask) -> None:
        app.config.setdefault('FIRST_RESPONSE_VALIDATION', False)
        register_errors(app)
        app.specification = self.mapping

        self._register_before_request_validation()

        if app.config['FIRST_RESPONSE_VALIDATION']:
            self._register_after_request_validation()

    def mapping(self, func) -> None:
        self._route_registration_in_flask(func)
