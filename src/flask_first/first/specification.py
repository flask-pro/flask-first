from copy import deepcopy
from pathlib import Path
from typing import Optional

from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from ..schema.schema_maker import make_marshmallow_schema
from .exceptions import FirstOpenAPIValidation
from .loaders import load_from_yaml
from .validator import OpenAPI310ValidationError
from .validator import Validator


class Specification:
    def __init__(
        self,
        path: Path or str,
        experimental_validator: bool = False,
        datetime_format: Optional[str] = None,
    ):
        self.path = path
        self.datetime_format = datetime_format
        self.experimental_validator = experimental_validator
        self.raw_spec = load_from_yaml(self.path)
        self._validating_openapi_file(self.path, self.experimental_validator)
        self.resolved_spec = self._convert_parameters_to_schema(self.raw_spec)
        self.serialized_spec = self._convert_schemas(self.resolved_spec)

    def _validating_openapi_file(self, path: Path, experimental_validator: bool):
        if experimental_validator:
            try:
                Validator(path).validate()
            except OpenAPI310ValidationError as e:
                raise FirstOpenAPIValidation(repr(e))

        try:
            validate(self.raw_spec)
        except (OpenAPIValidationError, TypeError) as e:
            raise FirstOpenAPIValidation(repr(e))

    @staticmethod
    def _make_param_schema(parameters: list, type_params: str) -> Optional[dict]:
        schema = {'type': 'object', 'additionalProperties': False, 'properties': {}}
        for param in parameters:
            if type_params != param['in']:
                continue

            schema['properties'][param['name']] = param['schema']
            required_param_list = schema.get('required')
            required_param = param.get('required')
            if required_param:
                if required_param_list:
                    schema['required'].append(param['name'])
                else:
                    schema['required'] = [param['name']]

        if schema['properties']:
            return schema
        else:
            return

    def _from_list_to_schemas(self, parameters: list) -> dict:
        view_args = self._make_param_schema(parameters, 'path')
        args = self._make_param_schema(parameters, 'query')
        header_args = self._make_param_schema(parameters, 'header')
        cookies = self._make_param_schema(parameters, 'cookie')

        schemas = {}
        if view_args:
            schemas['view_args'] = view_args
        if args:
            schemas['args'] = args
        if header_args:
            schemas['header_args'] = header_args
        if cookies:
            schemas['cookies'] = cookies

        return schemas

    def _convert_parameters_to_schema(self, spec_without_refs) -> dict:
        schema = deepcopy(spec_without_refs)
        for _, path_item in schema['paths'].items():
            common_parameters: Optional[list] = path_item.pop('parameters', [])
            for method, operation in path_item.items():
                parameters_from_method: Optional[list] = operation.get('parameters', [])

                combined_params = [*common_parameters, *parameters_from_method]

                if not combined_params:
                    continue

                parameters_schemas = self._from_list_to_schemas(combined_params)

                # Adding key `schema` for create regular structure. For simple using.
                path_item[method]['parameters'] = parameters_schemas
        return schema

    def _convert_schemas(self, resolved_schema: dict) -> dict or list:
        converted_schema = deepcopy(resolved_schema)
        if isinstance(converted_schema, dict):
            for key, value in converted_schema.items():
                if key in {'header_args', 'view_args', 'args', 'cookie'}:
                    converted_schema[key] = make_marshmallow_schema(
                        value, datetime_format=self.datetime_format
                    )
                elif key == 'schema':
                    converted_schema['schema'] = make_marshmallow_schema(
                        value, datetime_format=self.datetime_format
                    )
                elif key == 'schemas':
                    for schema_name, schema_value in value.items():
                        value[schema_name] = make_marshmallow_schema(
                            schema_value, datetime_format=self.datetime_format
                        )
                else:
                    converted_schema[key] = self._convert_schemas(value)
            return converted_schema

        if isinstance(converted_schema, list):
            schemas = []
            for schema in converted_schema:
                schemas.append(self._convert_schemas(schema))
            return schemas

        return converted_schema
