from typing import Iterable
from typing import List
from typing import Union

from marshmallow import fields
from marshmallow import INCLUDE
from marshmallow import Schema
from marshmallow import validate
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from marshmallow.fields import Field

from .exc import FlaskFirstPathParameterValidation
from .exc import FlaskFirstValidation

FIELDS_VIA_TYPES = {
    'boolean': fields.Boolean(),
    'number': fields.Float(),
    'string': fields.String(),
    'integer': fields.Integer(),
}

FIELDS_VIA_FORMATS = {
    'uuid': fields.UUID(),
    'date-time': fields.DateTime(),
    'date': fields.Date(),
    'time': fields.Time(),
    'email': fields.Email(),
    'ipv4': fields.IPv4(),
    'ipv6': fields.IPv6(),
    'url': fields.Url(),
}


def _make_field_for_schema(schema: dict) -> Field:
    if schema.get('format'):
        field = FIELDS_VIA_FORMATS[schema['format']]
    else:
        if schema['type_'] == 'array':
            if schema['items']['type_'] == 'object':
                nested_field = _make_json_schema(schema['items'])
                field = fields.Nested(nested_field, many=True)
            else:
                nested_field = FIELDS_VIA_TYPES[schema['items']['type_']]
                field = fields.List(nested_field)
        else:
            field = FIELDS_VIA_TYPES[schema['type_']]

        validators = []

        if schema['type_'] in ['string']:
            validators.append(
                validate.Length(min=schema.get('minLength'), max=schema.get('maxLength'))
            )

        if schema['type_'] in ['string']:
            validators.append(validate.Regexp(schema.get('pattern', r'^.*$')))

        if schema['type_'] in ['integer', 'number']:
            validators.append(validate.Range(min=schema.get('minimum'), max=schema.get('maximum')))

        field.validators = validators

    if schema.get('nullable'):
        field.allow_none = True

    return field


def _make_json_schema(schema: dict) -> type:
    fields = {}
    for field_name, field_schema in schema['properties'].items():
        field_to_schema = _make_field_for_schema(field_schema)

        if schema.get('required'):
            if field_name in schema['required']:
                field_to_schema.required = True

        fields[field_name] = field_to_schema

    return Schema.from_dict(fields)


def _make_parameter_schema(keys: Iterable, parameters: dict) -> type:
    schema_fields = {}
    for key in keys:
        try:
            schema = parameters[key]['schema']
        except KeyError:
            raise FlaskFirstValidation(f'Parameter <{key}> not found in specification!')

        field = _make_field_for_schema(schema)
        schema_fields[key] = field

    marshmallow_schema = Schema.from_dict(schema_fields)

    return marshmallow_schema


def validate_params(parameters: dict, schema: Union[dict, List[dict]]) -> dict:
    schema = _make_parameter_schema(parameters.keys(), schema)
    try:
        return schema().load(parameters)
    except MarshmallowValidationError as e:
        raise FlaskFirstPathParameterValidation(e)


def validate_json(json: Union[dict, List[dict]], schema: dict) -> None:
    try:
        if isinstance(json, list):
            new_schema = _make_json_schema(schema['items'])
            new_schema(many=True).load(json)

        elif schema.get('allOf'):
            for schema_item in schema['allOf']:
                new_schema = _make_json_schema(schema_item)
                new_schema(unknown=INCLUDE).load(json, partial=True)

        elif schema.get('oneOf'):
            errors = []
            for schema_item in schema['oneOf']:
                new_schema = _make_json_schema(schema_item)
                errors.append(new_schema().validate(json, partial=True))

            if errors.count({}) != 1:
                raise FlaskFirstValidation(errors)

        elif schema.get('anyOf'):
            errors = []
            for schema_item in schema['anyOf']:
                new_schema = _make_json_schema(schema_item)
                errors.append(new_schema().validate(json, partial=True))

            if errors.count({}) == 0:
                raise FlaskFirstValidation(errors)

        else:
            new_schema = _make_json_schema(schema)
            new_schema().load(json)

    except MarshmallowValidationError as e:
        raise FlaskFirstValidation(e)
