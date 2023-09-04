"""Flask extension for using “specification first” principle."""
import re
from pathlib import Path
from typing import Any

import marshmallow
from flask import Blueprint
from flask import Flask
from flask import render_template
from flask import Request
from flask import request
from flask import Response
from flask import send_file
from flask import url_for
from marshmallow.exceptions import ValidationError
from werkzeug.datastructures import Headers
from werkzeug.datastructures import MultiDict

from .first import RequestSerializer
from .first import Specification
from .first.exceptions import FirstException
from .first.exceptions import FirstResponseJSONValidation
from .first.exceptions import FirstValidation

__version__ = '0.14.2'


class First:
    """This class is used to generation routes from OpenAPI specification."""

    TYPES_IN_ROUTE_MAPPER = {'string': '', 'integer': 'int:', 'number': 'float:'}

    def __init__(
        self,
        path_to_spec: str | Path,
        app: Flask = None,
        swagger_ui_path: str | Path = None,
    ) -> None:
        self.app = app
        self.path_to_spec = path_to_spec
        self.swagger_ui_path = swagger_ui_path

        if self.app is not None:
            self.init_app(app)

        self.spec = Specification(path_to_spec)

        self._mapped_routes_from_spec = []

    @staticmethod
    def route_to_openapi_format(route: str) -> str:
        return route.replace('<', '{').replace('>', '}').replace('int:', '').replace('float:', '')

    def _route_registration_in_flask(self, func: callable) -> None:
        route = method = ''

        for path, path_item in self.spec.resolved_spec['paths'].items():
            for method_name, operation in path_item.items():
                if operation.get('operationId') == func.__name__:
                    route: str = path
                    method: str = method_name

        if not route:
            raise FirstException(f'Route function <{route}> not found in OpenAPI specification!')

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

    def _extract_data_from_request(
        self, request_obj: Request
    ) -> tuple[Any, str | None, Headers, dict[str, Any] | None, dict, dict, Any | None]:
        method = request_obj.method.lower()

        if request_obj.url_rule is not None:
            route = request_obj.url_rule.rule
        else:
            route = request_obj.url_rule

        headers = request_obj.headers

        view_args = request_obj.view_args

        args = self._resolved_params(request_obj.args)

        cookies = self._resolved_params(request_obj.cookies)

        if request_obj.is_json:
            json = request_obj.get_json()
        else:
            json = None

        return method, route, headers, view_args, args, cookies, json

    def _resolved_params(self, payload: MultiDict) -> dict:
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

    def _arg_to_list(self, args: dict, schema_fields: dict) -> dict:
        for arg in args:
            arg_value = schema_fields.get(arg, ...)

            if arg_value is ...:
                continue

            if isinstance(arg_value, marshmallow.fields.List) and not isinstance(args[arg], list):
                args[arg] = [args[arg]]

        return args

    def _registration_swagger_ui_blueprint(self, swagger_ui_path: str | Path) -> None:
        swagger_ui = Blueprint(
            'swagger_ui',
            __name__,
            static_folder='static',
            template_folder='templates',
            url_prefix=swagger_ui_path,
        )

        @swagger_ui.add_app_template_global
        def swagger_ui_static(filename):
            return url_for('swagger_ui.static', filename=filename)

        @swagger_ui.route('/')
        def swagger_ui_page():
            return render_template('swagger_ui/index.html', path_to_spec=self.path_to_spec)

        @swagger_ui.route('/openapi.yaml')
        def get_file_spec():
            return send_file(self.path_to_spec)

        self.app.register_blueprint(swagger_ui)

    def _register_request_validation(self) -> None:
        @self.app.before_request
        def add_request_validating() -> None:
            if request.content_type != 'application/json' and request.method not in ('GET',):
                return

            if request.method in ('OPTIONS',):
                return

            (
                method,
                route,
                headers,
                view_args,
                args,
                cookies,
                json,
            ) = self._extract_data_from_request(request)

            if route not in self._mapped_routes_from_spec:
                return

            route_as_in_spec = self.route_to_openapi_format(route)

            params_schemas = self.spec.serialized_spec['paths'][route_as_in_spec][method].get(
                'parameters'
            )
            if params_schemas:
                args_schema = params_schemas.get('args')
                if args_schema:
                    schema_fields = args_schema().fields
                    args = self._arg_to_list(args, schema_fields)

            rv = RequestSerializer(
                self.spec,
                method,
                route_as_in_spec,
                headers=dict(headers),
                cookies=cookies,
                path_params=view_args,
                params=args,
                json=json,
            )
            rv.validate()

            request.first_headers = rv.serialized_headers
            request.first_view_args = rv.serialized_path_params
            request.first_args = rv.serialized_params
            request.first_cookies = rv.serialized_cookies
            request.first_json = rv.serialized_json

    def _register_response_validation(self) -> None:
        @self.app.after_request
        def add_response_validating(response: Response) -> Response:
            method, route, _, _, _, _, json = self._extract_data_from_request(request)
            json = response.get_json()

            if route not in self._mapped_routes_from_spec:
                return response

            route_as_in_spec = self.route_to_openapi_format(route)

            try:
                route_schema: dict = self.spec.serialized_spec['paths'][route_as_in_spec]
            except KeyError as e:
                raise FirstResponseJSONValidation(
                    f'Route <{e.args[0]}> not defined in specification.'
                )

            try:
                method_schema: dict = route_schema[method]
            except KeyError as e:
                raise FirstResponseJSONValidation(
                    f'Method <{e.args[0]}> not defined in <{route_as_in_spec}>'
                )

            try:
                http_code_schema: dict = method_schema['responses'][str(response.status_code)]
            except KeyError as e:
                raise FirstResponseJSONValidation(
                    f'HTTP code <{e.args[0]}> not defined in route <{route_as_in_spec}>'
                )

            content: dict = http_code_schema['content']

            response_content_type = response.content_type

            if response_content_type not in content and '*/*' not in content:
                raise FirstValidation(
                    f'Content type <{response_content_type}> not in <{content.keys()}>'
                )

            if response_content_type == 'application/json':
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
                    raise FirstResponseJSONValidation(repr(e))

            return response

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.app.config.setdefault('FIRST_RESPONSE_VALIDATION', False)
        self.app.extensions['first'] = self

        if self.swagger_ui_path:
            self._registration_swagger_ui_blueprint(self.swagger_ui_path)

        self._register_request_validation()

        if self.app.config['FIRST_RESPONSE_VALIDATION']:
            self._register_response_validation()

    def add_view_func(self, func) -> None:
        self._route_registration_in_flask(func)
