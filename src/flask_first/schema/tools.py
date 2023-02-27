from copy import deepcopy

from .schema_maker import make_marshmallow_schema


def _resolving_all_refs(raw_schema: dict, schema: dict) -> dict | list:
    if isinstance(schema, dict):
        if '$ref' in schema:
            keys = schema['$ref'].replace('#/', '').split('/')

            schema_from_ref = deepcopy(raw_schema)
            for key in keys:
                schema_from_ref = schema_from_ref[key]

            return _resolving_all_refs(raw_schema, schema_from_ref)

        else:
            for key, value in schema.items():
                schema[key] = _resolving_all_refs(raw_schema, value)
        return schema

    if isinstance(schema, list):
        schemas = []
        for item in schema:
            schemas.append(_resolving_all_refs(raw_schema, item))
        return schemas

    return schema


def _from_list_to_schema(parameters: list) -> dict:
    schema = {'type': 'object', 'additionalProperties': False, 'properties': {}}
    for param in parameters:
        schema['properties'][param['name']] = param['schema']
        required_param_list = schema.get('required')
        required_param = param.get('required')
        if required_param:
            if required_param_list:
                schema['required'].append(param['name'])
            else:
                schema['required'] = [param['name']]
    return schema


def _convert_parameters_to_schema(resolved_schema: dict) -> dict:
    schema = deepcopy(resolved_schema)
    for _, path_item in schema['paths'].items():
        common_parameters: list | None = path_item.pop('parameters', [])
        for method, operation in path_item.items():
            parameters_from_method: list | None = operation.get('parameters', [])

            combined_params = [*common_parameters, *parameters_from_method]

            if not combined_params:
                continue

            parameters_schema = _from_list_to_schema(combined_params)

            # Adding key `schema` for create regular structure. For simple using.
            path_item[method]['parameters'] = {'schema': parameters_schema}
    return schema


def resolving_refs(raw_schema: dict) -> dict:
    schema = deepcopy(raw_schema)
    schema_without_refs = _resolving_all_refs(raw_schema, schema)
    resolved_schema = _convert_parameters_to_schema(schema_without_refs)
    return resolved_schema


def convert_schemas(resolved_schema: dict) -> dict | list:
    converted_schema = deepcopy(resolved_schema)
    if isinstance(converted_schema, dict):
        for key, value in converted_schema.items():
            if key == 'schema':
                converted_schema['schema'] = make_marshmallow_schema(value)
            elif key == 'schemas':
                for schema_name, schema_value in value.items():
                    value[schema_name] = make_marshmallow_schema(schema_value)
            else:
                converted_schema[key] = convert_schemas(value)
        return converted_schema

    if isinstance(converted_schema, list):
        schemas = []
        for schema in converted_schema:
            schemas.append(convert_schemas(schema))
        return schemas

    return converted_schema
