from copy import deepcopy
from pathlib import Path

from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from ..schema.schema_maker import make_marshmallow_schema
from .exceptions import FirstOpenAPIValidation


class Specification:
    def __init__(self, path: Path):
        self.raw_spec, _ = read_from_filename(path)
        self._validating_openapi_file()
        self.resolved_spec = self._resolving_refs()
        self.serialized_spec = self._convert_schemas(self.resolved_spec)

    def _validating_openapi_file(self):
        try:
            validate_spec(self.raw_spec)
        except OpenAPIValidationError as e:
            raise FirstOpenAPIValidation(repr(e))

    def _resolving_all_refs(self, schema: dict) -> dict | list:
        if isinstance(schema, dict):
            if '$ref' in schema:
                keys = schema['$ref'].replace('#/', '').split('/')

                schema_from_ref = deepcopy(self.raw_spec)
                for key in keys:
                    schema_from_ref = schema_from_ref[key]

                return self._resolving_all_refs(schema_from_ref)

            else:
                for key, value in schema.items():
                    schema[key] = self._resolving_all_refs(value)
            return schema

        if isinstance(schema, list):
            schemas = []
            for item in schema:
                schemas.append(self._resolving_all_refs(item))
            return schemas

        return schema

    def _make_param_schema(self, parameters: list, type_params: str) -> dict | None:
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
            common_parameters: list | None = path_item.pop('parameters', [])
            for method, operation in path_item.items():
                parameters_from_method: list | None = operation.get('parameters', [])

                combined_params = [*common_parameters, *parameters_from_method]

                if not combined_params:
                    continue

                parameters_schemas = self._from_list_to_schemas(combined_params)

                # Adding key `schema` for create regular structure. For simple using.
                path_item[method]['parameters'] = parameters_schemas
        return schema

    def _resolving_refs(self) -> dict:
        spec_without_refs = self._resolving_all_refs(self.raw_spec)
        resolved_schema = self._convert_parameters_to_schema(spec_without_refs)
        return resolved_schema

    def _convert_schemas(self, resolved_schema: dict) -> dict | list:
        converted_schema = deepcopy(resolved_schema)
        if isinstance(converted_schema, dict):
            for key, value in converted_schema.items():
                if key in {'header_args', 'view_args', 'args', 'cookie'}:
                    converted_schema[key] = make_marshmallow_schema(value)
                elif key == 'schema':
                    converted_schema['schema'] = make_marshmallow_schema(value)
                elif key == 'schemas':
                    for schema_name, schema_value in value.items():
                        value[schema_name] = make_marshmallow_schema(schema_value)
                else:
                    converted_schema[key] = self._convert_schemas(value)
            return converted_schema

        if isinstance(converted_schema, list):
            schemas = []
            for schema in converted_schema:
                schemas.append(self._convert_schemas(schema))
            return schemas

        return converted_schema
