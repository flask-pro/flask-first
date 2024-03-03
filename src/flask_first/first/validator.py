from pathlib import Path

import yaml
from marshmallow import fields
from marshmallow import pre_load
from marshmallow import Schema
from marshmallow import validate
from marshmallow import ValidationError

OPENAPI_VERSION = '3.1.0'
TYPES = ['array', 'boolean', 'integer', 'number', 'object', 'string']
RE_VERSION = r'^[0-9]+.[0-9]+.[0-9]+$'

ENDPOINT_FIELD = fields.String(required=True, validate=validate.Regexp(r'^[/][0-9a-z-{}/]*[^/]$'))
HTTP_CODE_FIELD = fields.String(required=True, validate=validate.Regexp(r'^[1-5]{1}\d{2}|default$'))
DESCRIPTION_FIELD = fields.String(required=True)
MEDIA_TYPE_FIELD = fields.String(required=True)


class OpenAPI310ValidationError(Exception):
    """OpenAPI specification validation error."""


class InfoSchema(Schema):
    title = fields.String(required=True)
    version = fields.String(required=True, validate=validate.Regexp(RE_VERSION))


class SchemaObjectSchema(Schema):
    type = fields.String(required=True, validate=validate.OneOf(TYPES))
    properties = fields.Dict(
        keys=fields.String(required=True), values=fields.Nested(lambda: SchemaObjectSchema())
    )


class MediaTypeObjectSchema(Schema):
    schema = fields.Nested(SchemaObjectSchema)


class ResponsesObjectSchema(Schema):
    description = DESCRIPTION_FIELD
    content = fields.Dict(keys=MEDIA_TYPE_FIELD, values=fields.Nested(MediaTypeObjectSchema))


class OperationObjectSchema(Schema):
    operation_id = fields.String(data_key='operationId')
    responses = fields.Dict(keys=HTTP_CODE_FIELD, values=fields.Nested(ResponsesObjectSchema))

    @pre_load
    def normalize_nested_keys(self, data, **kwargs):
        responses_with_key_as_str = {str(k): v for k, v in data['responses'].items()}
        data['responses'] = responses_with_key_as_str
        return data


class PathItemObjectSchema(Schema):
    get = fields.Nested(OperationObjectSchema)


class RootSchema(Schema):
    openapi = fields.String(
        required=True,
        validate=validate.And(
            validate.Equal(OPENAPI_VERSION), validate.Regexp(r'^[/][0-9a-z-{}/]*[^/]$')
        ),
    )
    info = fields.Nested(InfoSchema, required=True)
    paths = fields.Dict(
        required=True,
        keys=ENDPOINT_FIELD,
        values=fields.Nested(PathItemObjectSchema, required=True),
    )


class Validator:
    def __init__(self, path: Path or str):
        self.path = path
        self.raw_spec = self._yaml_to_dict(self.path)

    @staticmethod
    def _yaml_to_dict(path: Path) -> dict:
        with open(path) as f:
            s = yaml.safe_load(f)
        return s

    def validate(self) -> None or OpenAPI310ValidationError:
        try:
            RootSchema().validate(self.raw_spec)
        except ValidationError as e:
            raise OpenAPI310ValidationError(e)
