import re
import typing as t
from pathlib import Path
from typing import Any

from flask import Flask
from flask import request
from flask import Response
from flask.sansio.scaffold import T_route
from flask_first.first import RequestAdapter
from flask_first.first import ResponseAdapter
from schema_first import Specification
from schema_first.query.exceptions import EndpointValidation
from schema_first.query.validator import HTTPQueryValidator

from .first.exceptions import FirstException
from .swagger_ui import add_swagger_ui_blueprint


class First:
    """This class is used to generation routes from OpenAPI specification."""

    TYPES_IN_ROUTE_MAPPER = {'string': '', 'integer': 'int:', 'number': 'float:'}

    def __init__(
        self,
        path_to_spec: str or Path,
        app: Flask = None,
        swagger_ui_path: str or Path = None,
    ) -> None:
        self.app = app
        self.path_to_spec = path_to_spec
        self.swagger_ui_path = swagger_ui_path
        self.spec = Specification(self.path_to_spec).load()

        self.paths = {}
        self._map_rules_to_paths = {}

        if self.app is not None:
            self.init_app(self.app)

    @staticmethod
    def route_to_openapi_format(route: str) -> str:
        return route.replace('<', '{').replace('>', '}').replace('int:', '').replace('float:', '')

    def _get_param_schema(
        self, rule: str, method, part: t.Literal['headers', 'cookies', 'paths', 'queries']
    ) -> dict[str, Any] | None:
        path = self.spec.spilli_api['paths'][rule][method.lower()]

        parameters_from_method = path.get('parameters')
        if parameters_from_method:
            param_schema = parameters_from_method[part]['schema']
            return param_schema
        else:
            return None

    def _rule_convert_from_openapi_to_flask_format(self, rule: str, method: str):
        path_params = re.findall(r'{(\S*?)}', rule)
        if path_params:
            params_as_flask_format = {}
            for param_name in path_params:
                param_schema = self._get_param_schema(rule, method, 'paths')
                if param_schema is None:
                    raise NotImplementedError(
                        f'Parameters schema for <{rule}: {method}: paths> not found'
                    )

                param_type = param_schema['properties'][param_name]['type']
                params_as_flask_format[param_name] = (
                    f'<{self.TYPES_IN_ROUTE_MAPPER[param_type]}{param_name}>'
                )

            rule = rule.format(**params_as_flask_format)

        return rule

    def _route_registration_in_flask(
        self,
        path: str,
        func: t.Callable,
        methods: list[t.Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']] | None = None,
        **options,
    ) -> None:
        if methods is None:
            methods = ['GET']
        for method in methods:
            rule = self._rule_convert_from_openapi_to_flask_format(path, method)
            self._map_rules_to_paths[rule] = path
            self.app.add_url_rule(rule, func.__name__, func, methods=methods, **options)

    def _register_request_validation(self) -> None:
        @self.app.before_request
        def add_request_validating() -> None:
            prepared_request = RequestAdapter(
                request, self._map_rules_to_paths, self.spec
            ).to_dict()

            try:
                query_validator = HTTPQueryValidator(self.spec)
                deserialized_request = query_validator.request_handler(**prepared_request)
            except EndpointValidation:
                return

            request.extensions = {'first': deserialized_request}

    def _register_response_validation(self) -> None:
        @self.app.after_request
        def add_response_validating(response: Response) -> Response:
            prepared_response = ResponseAdapter(
                request, response, self._map_rules_to_paths, self.spec
            ).to_dict()

            try:
                query_validator = HTTPQueryValidator(self.spec)
                query_validator.response_handler(**prepared_response)
            except EndpointValidation:
                return response

            return response

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.app.config.setdefault('FIRST_RESPONSE_VALIDATION', False)
        self.app.config.setdefault('FIRST_EXPERIMENTAL_VALIDATOR', False)
        self.app.config.setdefault('FIRST_DATETIME_FORMAT', None)
        self.app.extensions['first'] = self

        if self.swagger_ui_path:
            add_swagger_ui_blueprint(self.app, self.spec, self.swagger_ui_path)

        self._register_request_validation()

        if self.app.config['FIRST_RESPONSE_VALIDATION']:
            self._register_response_validation()

        for rule, options in self.paths.items():
            self._route_registration_in_flask(rule, **options)

    def route(
        self,
        rule: str,
        methods: list[t.Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']] | None = None,
        **options: t.Any,
    ) -> t.Callable[[T_route], T_route]:

        if methods is None:
            methods = ['GET']

        def decorator(f: T_route) -> T_route:
            if rule in self.paths:
                raise FirstException(f'Rule <{rule}> exits.')

            for method in methods:
                route = self.spec.reassembly_spec['paths'].get(rule)
                if not route:
                    raise FirstException(f'Route <{rule}> not exist in OpenAPI specification.')

                method = route.get(method)
                if not route:
                    raise FirstException(
                        f'Route <{rule}> for method <{method}> not exist in OpenAPI specification.'
                    )

            self.paths[rule] = {'func': f, 'methods': methods, **options}

            return f

        return decorator
