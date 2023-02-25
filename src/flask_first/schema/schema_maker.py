from marshmallow import fields
from marshmallow import Schema
from marshmallow import validate
from marshmallow import ValidationError

from .custom_fields import AllOf
from .custom_fields import AnyOf
from .custom_fields import OneOf


class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')


FIELDS_VIA_TYPES = {
    'boolean': fields.Boolean,
    'number': fields.Float,
    'string': fields.String,
    'integer': fields.Integer,
}

FIELDS_VIA_FORMATS = {
    'uuid': fields.UUID,
    'date-time': fields.DateTime,
    'date': fields.Date,
    'time': fields.Time,
    'email': fields.Email,
    'ipv4': fields.IPv4,
    'ipv6': fields.IPv6,
    'url': fields.Url,
    'binary': BytesField,
}


def _make_object_field(schema: dict, as_nested: bool = True) -> fields.Nested | type:
    fields_obj = {}
    for field_name, field_schema in schema['properties'].items():
        if field_schema['type'] == 'object':
            field = make_marshmallow_schema(field_schema, as_nested=True)
        else:
            field = make_marshmallow_schema(field_schema)

        if field_name in schema.get('required', ()):
            field.required = True

        fields_obj[field_name] = field

    schema_object = Schema.from_dict(fields_obj)

    if as_nested:
        return fields.Nested(schema_object)
    else:
        return schema_object


def _make_array_field(schema: dict) -> fields.Field:
    data_type = schema['items']['type']
    data_format = schema['items'].get('format')
    if data_type == 'object':
        nested_field = _make_object_field(schema['items'])
        nested_field.many = True
        field = nested_field
    elif data_format in FIELDS_VIA_FORMATS:
        nested_field = FIELDS_VIA_FORMATS[data_format]()
        field = fields.List(nested_field)
    else:
        nested_field = FIELDS_VIA_TYPES[data_type]()
        field = fields.List(nested_field)

    return field


def _make_multiple_field(schema: dict) -> type:
    marshmallow_schemas = []
    multiple_field_name = None

    for key in schema:
        if key in ('oneOf', 'anyOf', 'allOf'):
            multiple_field_name = key
            break
        else:
            raise NotImplementedError('Not available multi-schema.')

    for schema_item in schema[multiple_field_name]:
        marshmallow_schemas.append(make_marshmallow_schema(schema_item))

    if 'oneOf' in multiple_field_name:
        schema_multiple_field = Schema.from_dict({multiple_field_name: OneOf(*marshmallow_schemas)})
    elif 'anyOf' in multiple_field_name:
        schema_multiple_field = Schema.from_dict({multiple_field_name: AnyOf(*marshmallow_schemas)})
    elif 'allOf' in multiple_field_name:
        schema_multiple_field = Schema.from_dict({multiple_field_name: AllOf(*marshmallow_schemas)})
    else:
        raise NotImplementedError('Not available schema.')

    return schema_multiple_field


def _make_field_validators(schema: dict) -> list[validate.Validator]:
    validators = []

    if schema['type'] in ['string']:
        validators.append(validate.Length(min=schema.get('minLength'), max=schema.get('maxLength')))
        validators.append(validate.Regexp(schema.get('pattern', r'^.*$')))

    if schema['type'] in ['integer', 'number']:
        validators.append(validate.Range(min=schema.get('minimum'), max=schema.get('maximum')))

    return validators


def make_marshmallow_schema(schema: dict, as_nested: bool = False) -> fields.Field:
    if 'nullable' in schema and schema.get('type', ...) is ...:
        field = FIELDS_VIA_TYPES['boolean']()
    elif 'allOf' in schema:
        field = _make_multiple_field(schema)
    elif 'anyOf' in schema:
        field = _make_multiple_field(schema)
    elif 'oneOf' in schema:
        field = _make_multiple_field(schema)
    elif schema.get('format'):
        field = FIELDS_VIA_FORMATS[schema['format']]()
    elif schema['type'] == 'object':
        field = _make_object_field(schema, as_nested=as_nested)
    elif schema['type'] == 'array':
        field = _make_array_field(schema)
    else:
        field = FIELDS_VIA_TYPES[schema['type']]()

        field.validators = _make_field_validators(schema)

    if schema.get('nullable'):
        field.allow_none = True

    return field
