"""Flask extension for using “specification first” principle."""
from pathlib import Path
from typing import List
from typing import Optional
from typing import Union

from flask import Blueprint
from flask import Flask
from flask import render_template
from flask import Request
from flask import request
from flask import Response
from flask import send_file
from flask import url_for
from jsonschema.exceptions import ValidationError
from jsonschema.validators import RefResolver
from openapi_schema_validator import oas30_format_checker
from openapi_schema_validator import validate
from openapi_spec_validator import validate_spec
from openapi_spec_validator.exceptions import OpenAPIValidationError
from openapi_spec_validator.readers import read_from_filename
from werkzeug.datastructures import MultiDict

from .exceptions import FirstException
from .exceptions import FirstOpenAPIValidation
from .exceptions import FirstRequestArgsValidation
from .exceptions import FirstRequestJSONValidation
from .exceptions import FirstRequestPathParamValidation
from .exceptions import FirstResponseJSONValidation
from .exceptions import register_errors
from .schema_maker import make_marshmallow_schema

__version__ = '0.9.0'


class First:
    """This class is used to generation routes from OpenAPI specification."""

    def __init__(
        self,
        path_to_spec: Union[str, Path],
        app: Flask = None,
        swagger_ui_path: Union[str, Path] = None,
    ) -> None:
        self.app = app
        self.path_to_spec = path_to_spec
        self.swagger_ui_path = swagger_ui_path

        if self.app is not None:
            self.init_app(app)

        self.spec, _ = read_from_filename(path_to_spec)
        try:
            validate_spec(self.spec)
        except OpenAPIValidationError as e:
            raise FirstOpenAPIValidation(repr(e))

        self.ref_resolver = RefResolver.from_schema(self.spec)

        self._mapped_routes_from_spec = []

    @staticmethod
    def route_to_openapi_format(route: str) -> str:
        return route.replace('<', '{').replace('>', '}').replace('int:', '').replace('float:', '')

    def _route_registration_in_flask(self, func: callable) -> None:
        route = method = ''

        for path, path_item in self.spec['paths'].items():
            for method_name, operation in path_item.items():
                if method_name == 'parameters':
                    continue
                if operation.get('operationId') == func.__name__:
                    route: str = path
                    method: str = method_name

        if not route:
            raise FirstException(f'Route function <{route}> not found in OpenAPI specification!')

        _, path_schema, _, _ = self._make_schemas_params(method, route)

        if path_schema:
            path_params = {}
            for parameter, schema in path_schema['properties'].items():
                path_params.update({parameter: f'<{schema["type"]}:{parameter}>'})

            rule = route.format(**path_params)
            rule = (
                rule.replace('string:', '').replace('integer:', 'int:').replace('number:', 'float:')
            )
        else:
            rule = route

        self.app.add_url_rule(rule, func.__name__, func, methods=[method.upper()])

        self._mapped_routes_from_spec.append(rule)

    def _extract_data_from_request(self, request_obj: Request) -> tuple:
        method = request_obj.method.lower()

        if request_obj.url_rule is not None:
            route = request_obj.url_rule.rule
        else:
            route = request_obj.url_rule

        path_parameters = request_obj.view_args
        args = request_obj.args
        json = request_obj.json
        return method, route, path_parameters, args, json

    def _make_schema_params(self, param_type: str, schemas: List[dict]) -> Optional[dict]:
        properties = {}
        required = []
        for schema in schemas:
            if '$ref' in schema:
                with self.ref_resolver.resolving(schema['$ref']) as resolved_schema:
                    schema = resolved_schema

            if schema.get('required') is True:
                required.append(schema['name'])
            if schema['in'] == param_type:
                properties[schema['name']] = schema['schema']

        if properties:
            new_schema = {'type': 'object', 'properties': properties}
            if required:
                new_schema['required'] = required
            return new_schema
        else:
            return None

    def _make_schemas_params(self, method: str, route: str) -> tuple:
        schemas_params = []

        try:
            common_params: dict = self.spec['paths'][route].get('parameters')
            if common_params:
                schemas_params.extend(common_params)
        except KeyError:
            raise FirstException(f'Route <{request.endpoint}> not found in specification!')

        try:
            personal_params: dict = self.spec['paths'][route][method].get('parameters')
            if personal_params:
                schemas_params.extend(personal_params)
        except KeyError:
            raise FirstException(f'Method <{method}> not found in route <{request.endpoint}>!')

        # Create schema as object from parameters list.
        headers_schema = self._make_schema_params('header', schemas_params)
        path_schema = self._make_schema_params('path', schemas_params)
        args_schema = self._make_schema_params('query', schemas_params)
        cookie_schema = self._make_schema_params('cookie', schemas_params)

        return headers_schema, path_schema, args_schema, cookie_schema

    def _args_to_dict(self, args: MultiDict, schema: dict) -> dict:
        rendered_args = {}
        for key, value in args.to_dict(flat=False).items():
            if len(value) == 1:
                rendered_args[key] = value[0]
            if len(value) > 1:
                rendered_args[key] = value

        marshmallow_schema = make_marshmallow_schema(schema)
        return marshmallow_schema().load(rendered_args)

    def _registration_swagger_ui_blueprint(self, swagger_ui_path: Union[str, Path]) -> None:
        swagger_ui = Blueprint(
            'swagger_ui',
            __name__,
            static_folder='static',
            template_folder='templates',
            url_prefix=swagger_ui_path,
        )

        @swagger_ui.add_app_template_global
        def swagger_ui_static(filename):
            return url_for("swagger_ui.static", filename=filename)

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
            method, route, path_params, args, json = self._extract_data_from_request(request)

            if route not in self._mapped_routes_from_spec:
                return

            route_as_in_spec = self.route_to_openapi_format(route)
            _, path_schema, args_schema, _ = self._make_schemas_params(method, route_as_in_spec)

            if path_params:
                try:
                    validate(
                        path_params,
                        path_schema,
                        format_checker=oas30_format_checker,
                        resolver=self.ref_resolver,
                    )
                except ValidationError as e:
                    raise FirstRequestPathParamValidation(e)

            if args:
                try:
                    request.first_args = self._args_to_dict(args, args_schema)
                    validate(
                        request.first_args,
                        args_schema,
                        format_checker=oas30_format_checker,
                        resolver=self.ref_resolver,
                    )
                except ValidationError as e:
                    raise FirstRequestArgsValidation(e)

            if json:
                json_request_schema = self.spec['paths'][route_as_in_spec][method]['requestBody'][
                    'content'
                ][request.content_type]['schema']
                try:
                    validate(
                        request.json,
                        json_request_schema,
                        format_checker=oas30_format_checker,
                        resolver=self.ref_resolver,
                    )
                except ValidationError as e:
                    raise FirstRequestJSONValidation(str(e))

    def _register_response_validation(self) -> None:
        @self.app.after_request
        def add_response_validating(response: Response) -> Response:
            method, route, _, _, _ = self._extract_data_from_request(request)

            if route not in self._mapped_routes_from_spec:
                return response

            route_as_in_spec = self.route_to_openapi_format(route)
            json_response_schema = self.spec['paths'][route_as_in_spec][method]['responses'][
                str(response.status_code)
            ]['content'][response.content_type]['schema']

            try:
                validate(
                    response.json,
                    json_response_schema,
                    format_checker=oas30_format_checker,
                    resolver=self.ref_resolver,
                )
                return response
            except ValidationError as e:
                raise FirstResponseJSONValidation(e)

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.app.config.setdefault('FIRST_RESPONSE_VALIDATION', False)
        register_errors(self.app)
        self.app.extensions['first'] = self

        if self.swagger_ui_path:
            self._registration_swagger_ui_blueprint(self.swagger_ui_path)

        self._register_request_validation()

        if self.app.config['FIRST_RESPONSE_VALIDATION']:
            self._register_response_validation()

    def add_view_func(self, func) -> None:
        self._route_registration_in_flask(func)
