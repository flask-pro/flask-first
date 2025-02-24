import re
from pathlib import Path

import marshmallow
from flask import Flask
from flask import Request
from flask import request
from flask import Response
from marshmallow.exceptions import ValidationError
from werkzeug.datastructures import MultiDict

from .first import RequestSerializer
from .first import Specification
from .first.exceptions import FirstException
from .first.exceptions import FirstResponseJSONValidation
from .first.exceptions import FirstValidation
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
        self.spec = None

        if self.app is not None:
            self.init_app(app)

        self._mapped_routes_from_spec = []

    @staticmethod
    def route_to_openapi_format(route: str) -> str:
        return route.replace('<', '{').replace('>', '}').replace('int:', '').replace('float:', '')

    def _route_registration_in_flask(self, func: callable) -> None:
        route = method = ''

        for path, path_item in self.spec.resolved_spec['paths'].items():
            for method_name, operation in path_item.items():
                route_from_spec = operation.get('operationId')
                if route_from_spec == func.__name__:
                    route: str = path
                    method: str = method_name

        if not route:
            raise FirstException(
                f'Route function <{func.__name__}> not found in OpenAPI specification!'
            )

        params_schema = self.spec.resolved_spec['paths'][route][method].get('parameters')

        if params_schema and '{' in route and '}' in route:
            path_params = re.findall(r'{(\S*?)}', route)

            params_as_flask_format = {}
            for param in path_params:
                param_type = params_schema['view_args']['properties'][param]['type']
                params_as_flask_format[param] = f'<{self.TYPES_IN_ROUTE_MAPPER[param_type]}{param}>'

            rule = route.format(**params_as_flask_format)
        else:
            rule = route

        self.app.add_url_rule(rule, func.__name__, func, methods=[method.upper()])

        self._mapped_routes_from_spec.append(rule)

    @staticmethod
    def _extract_method_from_request(request_obj: Request) -> str:
        return request_obj.method.lower()

    @staticmethod
    def _extract_route_from_request(request_obj: Request) -> str:
        if request_obj.url_rule is not None:
            route = request_obj.url_rule.rule
        else:
            route = request_obj.url_rule

        return route

    @staticmethod
    def _extract_json_from_request(request_obj: Request) -> dict or None:
        if request_obj.is_json:
            json = request_obj.get_json()
        else:
            json = None

        return json

    @staticmethod
    def _resolved_params(payload: MultiDict) -> dict:
        # payload.to_dict(flat=False) serializing all arguments as list for correct receipt of
        # arguments of same name:
        # {'first_arg': ['1'], 'second_arg': ['10'], 'args_list': ['1', '2']}

        serialized_payload = {}
        for key, value in payload.to_dict(flat=False).items():
            if len(value) == 1:
                serialized_payload[key] = value[0]
            else:
                serialized_payload[key] = value

        return serialized_payload

    @staticmethod
    def _arg_to_list(args: dict, schema_fields: dict) -> dict:
        for arg in args:
            arg_value = schema_fields.get(arg, ...)

            if arg_value is ...:
                continue

            if isinstance(arg_value, marshmallow.fields.List) and not isinstance(args[arg], list):
                args[arg] = [args[arg]]

        return args

    def _register_request_validation(self) -> None:
        @self.app.before_request
        def add_request_validating() -> None:
            if request.content_type != 'application/json' and request.method not in ('GET',):
                return

            if request.method in ('OPTIONS',):
                return

            route = self._extract_route_from_request(request)
            if route not in self._mapped_routes_from_spec:
                return

            route_as_in_spec = self.route_to_openapi_format(route)

            method = self._extract_method_from_request(request)
            params_schemas = self.spec.serialized_spec['paths'][route_as_in_spec][method].get(
                'parameters'
            )
            args = self._resolved_params(request.args)
            if params_schemas:
                args_schema = params_schemas.get('args')
                if args_schema:
                    schema_fields = args_schema().fields
                    args = self._arg_to_list(args, schema_fields)

            headers = request.headers
            view_args = request.view_args
            cookies = self._resolved_params(request.cookies)
            json = self._extract_json_from_request(request)

            request_serializer = RequestSerializer(
                self.spec,
                method,
                route_as_in_spec,
                headers=dict(headers),
                cookies=cookies,
                path_params=view_args,
                params=args,
                json=json,
            )
            request_serializer.validate()

            request.extensions = {
                'first': {
                    'headers': request_serializer.serialized_headers,
                    'view_args': request_serializer.serialized_path_params,
                    'args': request_serializer.serialized_params,
                    'cookies': request_serializer.serialized_cookies,
                    'json': request_serializer.serialized_json,
                }
            }

    def _register_response_validation(self) -> None:
        @self.app.after_request
        def add_response_validating(response: Response) -> Response:
            route = self._extract_route_from_request(request)
            if route not in self._mapped_routes_from_spec:
                return response

            route_as_in_spec = self.route_to_openapi_format(route)

            try:
                route_schema: dict = self.spec.serialized_spec['paths'][route_as_in_spec]
            except KeyError as e:
                raise FirstResponseJSONValidation(
                    f'Route <{e.args[0]}> not defined in specification.'
                )

            method = self._extract_method_from_request(request)
            try:
                method_schema: dict = route_schema[method]
            except KeyError as e:
                raise FirstResponseJSONValidation(
                    f'Method <{e.args[0]}> not defined in <{route_as_in_spec}>'
                )

            http_code_schema: dict = method_schema['responses'].get(str(response.status_code))
            if http_code_schema is None:
                try:
                    http_code_schema: dict = method_schema['responses']['default']
                except KeyError as e:
                    raise FirstResponseJSONValidation(
                        f'HTTP code <{str(response.status_code)}> or <{e.args[0]}> '
                        f'responses not defined in route <{route_as_in_spec}>'
                    )

            content: dict = http_code_schema['content']

            response_content_type = response.content_type

            if response_content_type not in content and '*/*' not in content:
                raise FirstValidation(
                    f'Content type <{response_content_type}> not in <{content.keys()}>'
                )

            if response_content_type == 'application/json':
                json = response.get_json()
                json_schema = content[response.content_type]['schema']
                try:
                    if isinstance(json, list):
                        json_schema._load(json, None)
                    elif 'allOf' in json_schema._declared_fields:
                        json_schema().load({'allOf': json})
                    elif 'anyOf' in json_schema._declared_fields:
                        json_schema().load({'anyOf': json})
                    elif 'oneOf' in json_schema._declared_fields:
                        json_schema().load({'oneOf': json})
                    else:
                        json_schema().load(json)
                except ValidationError as e:
                    raise FirstResponseJSONValidation(
                        f'For <{method} {route}> and response body <{json}> raised error'
                        f' <{repr(e)}>'
                    )

            return response

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.app.config.setdefault('FIRST_RESPONSE_VALIDATION', False)
        self.app.config.setdefault('FIRST_EXPERIMENTAL_VALIDATOR', False)
        self.app.config.setdefault('FIRST_DATETIME_FORMAT', None)
        self.app.extensions['first'] = self

        self.spec = Specification(
            self.path_to_spec,
            experimental_validator=self.app.config['FIRST_EXPERIMENTAL_VALIDATOR'],
            datetime_format=self.app.config['FIRST_DATETIME_FORMAT'],
        )

        if self.swagger_ui_path:
            add_swagger_ui_blueprint(self.app, self.spec, self.swagger_ui_path)

        self._register_request_validation()

        if self.app.config['FIRST_RESPONSE_VALIDATION']:
            self._register_response_validation()

    def add_view_func(self, func) -> None:
        self._route_registration_in_flask(func)
