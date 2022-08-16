from marshmallow import fields
from marshmallow import Schema
from marshmallow import validate


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
}


def _make_object_field(schema: dict, as_nested: bool = True) -> fields.Nested | type:
    fields_for_nested_schema = {}
    for field_name, field_schema in schema['properties'].items():
        field = _make_field_for_schema(field_schema)

        if field_name in schema.get('required', ()):
            field.required = True

        fields_for_nested_schema[field_name] = field

    schema_object = Schema.from_dict(fields_for_nested_schema)

    if as_nested:
        return fields.Nested(schema_object)
    else:
        return schema_object


def _make_array_field(schema: dict) -> fields.Field:
    data_type = schema['items']['type']
    data_format = schema['items'].get('format')
    if data_type == 'object':
        nested_field = _make_field_for_schema(schema['items'])
        nested_field.many = True
        field = nested_field
    elif data_format and data_format in FIELDS_VIA_FORMATS:
        nested_field = FIELDS_VIA_FORMATS[data_format]()
        field = fields.List(nested_field)
    else:
        nested_field = FIELDS_VIA_TYPES[data_type]()
        field = fields.List(nested_field)

    return field


def _make_field_validators(schema: dict) -> list[validate.Validator]:
    validators = []

    if schema['type'] in ['string']:
        validators.append(validate.Length(min=schema.get('minLength'), max=schema.get('maxLength')))
        validators.append(validate.Regexp(schema.get('pattern', r'^.*$')))

    if schema['type'] in ['integer', 'number']:
        validators.append(validate.Range(min=schema.get('minimum'), max=schema.get('maximum')))

    return validators


def _make_field_for_schema(schema: dict) -> fields.Field:
    if schema.get('format'):
        field = FIELDS_VIA_FORMATS[schema['format']]()
    else:
        if schema['type'] == 'object':
            field = _make_object_field(schema)
        elif schema['type'] == 'array':
            field = _make_array_field(schema)
        else:
            field = FIELDS_VIA_TYPES[schema['type']]()

        field.validators = _make_field_validators(schema)

    if schema.get('nullable'):
        field.allow_none = True

    return field


def make_marshmallow_schema(schema: dict) -> type:
    return _make_object_field(schema, as_nested=False)
