from collections.abc import Hashable
from collections.abc import Mapping
from copy import deepcopy
from functools import reduce
from pathlib import Path
from typing import Any
from typing import Optional

from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from ..schema.schema_maker import make_marshmallow_schema
from .exceptions import FirstOpenAPIResolverError
from .exceptions import FirstOpenAPIValidation
from .validator import OpenAPI310ValidationError
from .validator import Validator


class Resolver:
    """
    This class creates a dictionary from the specification that contains resolved schema references.
    Specification from several files are supported.
    """

    def __init__(self, abs_path: Path or str):
        self.abs_path = Path(abs_path)
        self.root_dir = self.abs_path.resolve().parent

    @staticmethod
    def file_to_dict(abs_path: Path) -> Mapping[Hashable, Any]:
        try:
            spec_as_dict, _ = read_from_filename(str(abs_path))
        except OSError as e:
            raise FirstOpenAPIResolverError(e)
        return spec_as_dict

    @staticmethod
    def get_value_of_key_from_dict(source_dict: dict, key: Hashable) -> Any or KeyError:
        return source_dict[key]

    def _get_schema_via_local_ref(self, root_schema: dict, keys: dict) -> dict:
        try:
            return reduce(self.get_value_of_key_from_dict, keys, root_schema)
        except KeyError:
            raise FirstOpenAPIResolverError(f'No such path: {keys}')

    def _get_schema_from_file_ref(self, root_dir: Path, relative_path: Path, keys: dict) -> dict:
        abs_path_file = Path(root_dir, relative_path)
        root_schema = self.file_to_dict(abs_path_file)
        return self._get_schema_via_local_ref(root_schema, keys)

    def _resolving(self, schema: dict, relative_path_to_file_schema: str) -> dict or list[dict]:
        if isinstance(schema, dict):
            if '$ref' in schema:
                try:
                    relative_file_path_from_ref, local_path = schema['$ref'].split('#/')
                except AttributeError:
                    raise FirstOpenAPIResolverError(f'"$ref" <{schema["$ref"]}> must be string.')

                local_path_parts = local_path.split('/')

                if relative_file_path_from_ref:
                    schema_from_ref = self._get_schema_from_file_ref(
                        self.root_dir, relative_file_path_from_ref, local_path_parts
                    )
                    schema = self._resolving(schema_from_ref, relative_file_path_from_ref)
                else:
                    schema_from_ref = self._get_schema_from_file_ref(
                        self.root_dir, relative_path_to_file_schema, local_path_parts
                    )
                    schema = self._resolving(schema_from_ref, relative_path_to_file_schema)

            else:
                for key, value in schema.items():
                    schema[key] = self._resolving(value, relative_path_to_file_schema)

            return schema

        if isinstance(schema, list):
            schemas = []
            for item in schema:
                schemas.append(self._resolving(item, relative_path_to_file_schema))
            return schemas

        return schema

    def resolve(self) -> Mapping[Hashable, Any]:
        schema = self.file_to_dict(self.abs_path)
        return self._resolving(schema, self.abs_path)


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
        self.raw_spec = Resolver(self.path).resolve()
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
