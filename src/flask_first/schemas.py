"""The module contains Marshmallow schemas for serializing the specification."""
from typing import Any

from marshmallow import fields
from marshmallow import pre_load
from marshmallow import Schema
from marshmallow import validate
from marshmallow import validates_schema
from marshmallow import ValidationError

VALUE_TYPES = ['boolean', 'object', 'array', 'number', 'string', 'integer']

SECURITY_TYPES = ['apiKey', 'http', 'oauth2', 'openIdConnect']

MEDIA_TYPES = [
    '*/*',
    'application/json',
    'application/xml',
    'text/html',
    'text/plain',
    'multipart/form-data',
    'application/x-www-form-urlencoded',
]

PARAMETER_LOCATIONS = ['path', 'query', 'header', 'cookie']
PARAMETER_STYLES = [
    'matrix',
    'label',
    'form',
    'simple',
    'spaceDelimited',
    'pipeDelimited',
    'deepObject',
]

# Regexp`s.
RE_REF = r'^#/components/[a-z]*/[a-zA-Z_]*$'
RE_OPERATION_ID = r'^[a-z_]{1}[a-zA-Z0-9_ -]+$'
RE_PARAMETER_NAME = r'^[a-zA-Z/{}_\-0-9]+$'
RE_ROUTE_PATH = r'^/[a-zA-Z/{}_\-0-9.]*$'
RE_RESPONSE_STATUS_CODE = r'^[0-9]{3}$|^default$'

# Fields for schemas.
enum = fields.List(fields.String())
description = fields.String()
example = fields.Raw()
summary = fields.String()
required = fields.Boolean()
style = fields.String(validate=validate.OneOf(PARAMETER_STYLES))
deprecated = fields.Boolean()
name = fields.String()
url = fields.URL()
operation_id = fields.String(validate=validate.Regexp(RE_OPERATION_ID))


def get_obj_via_reference(ref: str, raw_spec: dict) -> dict:
    keys_from_ref = ref.split('/')[1:]

    value_from_ref = raw_spec
    for key in keys_from_ref:
        value_from_ref = value_from_ref[key]

    return value_from_ref


class BaseSchema(Schema):
    @pre_load
    def preprocess_reference(self, data, **kwargs):
        if data.get('$ref'):
            self.resolve_reference(data)
        return data

    @pre_load
    def preprocess_parameters(self, data, **kwargs):
        if isinstance(data.get('parameters'), list):
            parameters = {}
            for param in data['parameters']:
                if param.get('$ref'):
                    self.resolve_reference(param)
                parameters[param['name']] = param
            data['parameters'] = parameters
        return data

    def resolve_reference(self, data: Any) -> None:
        if data.get('$ref'):
            schema_via_reference = get_obj_via_reference(data['$ref'], self.context['raw_spec'])
            data.update(schema_via_reference)
            data.pop('$ref')


class ServerVariableObjectSchema(BaseSchema):
    enum = enum
    default = fields.String(required=True)
    description = description


class ExternalDocumentationObjectSchema(BaseSchema):
    description = description
    url = fields.URL(required=True)


class ContactObjectSchema(BaseSchema):
    name = name
    url = url
    email = fields.Email()


class LicenseObjectSchema(BaseSchema):
    name = fields.String(required=True)
    url = url


class OAuthFlowObjectSchema(BaseSchema):
    authorizationUrl = fields.URL(required=True)
    tokenUrl = fields.URL(required=True)
    refreshUrl = fields.URL()
    scopes = fields.Dict(fields.String(), fields.String(), required=True)


class ExampleObjectSchema(BaseSchema):
    summary = summary
    description = description
    value = fields.Raw()
    externalValue = fields.URL()


class ServerObjectSchema(BaseSchema):
    url = fields.String(required=True)
    description = description
    variables = fields.Dict(fields.String(), fields.Nested(ServerVariableObjectSchema))


class LinkObjectSchema(BaseSchema):
    operationRef = fields.String()
    operationId = operation_id
    parameters = fields.Dict(fields.String(), fields.String())
    requestBody = fields.String()
    description = description
    server = fields.Nested(ServerObjectSchema)

    @validates_schema
    def validate_operationRef_field(self, data, **kwargs):
        if data.get('operationRef') and data.get('operationId'):
            raise ValidationError(
                '<operationRef> field is mutually exclusive of the <operationId> field!'
            )


class SchemaObjectSchema(BaseSchema):
    allOf = fields.Nested('SchemaObjectSchema', many=True)
    oneOf = fields.Nested('SchemaObjectSchema', many=True)
    anyOf = fields.Nested('SchemaObjectSchema', many=True)
    type_ = fields.String(data_key='type', validate=validate.OneOf(VALUE_TYPES))
    example = example
    minimum = fields.Float(strict=True)
    maximum = fields.Float(strict=True)
    minLength = fields.Integer(strict=True, validate=validate.Range(min=0))
    maxLength = fields.Integer(strict=True, validate=validate.Range(min=0))
    format = fields.String()
    required = fields.List(fields.String())
    additionalProperties = fields.Raw()
    properties = fields.Dict(
        fields.String(validate=validate.Regexp(RE_OPERATION_ID)),
        fields.Nested('SchemaObjectSchema'),
    )
    items = fields.Nested('SchemaObjectSchema')
    description = description
    default = fields.Raw()
    enum = enum
    nullable = fields.Boolean()

    @validates_schema
    def validate_additional_properties_field(self, data, **kwargs):
        if data.get('additionalProperties') is not None:
            if not isinstance(data['additionalProperties'], bool):
                errors = self.validate(data['additionalProperties'])
                if errors:
                    raise ValidationError(errors)

        if data.get('items') and data.get('type_') != 'array':
            raise ValidationError('<items> MUST be present if the type is array.')


class MediaTypeObjectSchema(BaseSchema):
    schema = fields.Nested(SchemaObjectSchema)
    examples = fields.Dict(fields.String(required=True), fields.Nested(ExampleObjectSchema))
    example = example


class RequestBodyObjectSchema(BaseSchema):
    description = description
    content = fields.Dict(
        fields.String(required=True, validate=validate.OneOf(MEDIA_TYPES)),
        fields.Nested(MediaTypeObjectSchema, required=True),
        required=True,
    )
    required = required


class HeaderObjectSchema(BaseSchema):
    description = description
    required = required
    schema = fields.Nested(SchemaObjectSchema)
    style = style


class ResponseObjectSchema(BaseSchema):
    """Response is similar to request."""

    description = fields.String(required=True)
    headers = fields.Dict(
        fields.String(required=True),
        fields.Nested(HeaderObjectSchema, required=True),
    )
    content = fields.Dict(
        fields.String(required=True, validate=validate.OneOf(MEDIA_TYPES)),
        fields.Nested(MediaTypeObjectSchema, required=True),
    )
    links = fields.Dict(fields.String(required=True), fields.Nested(LinkObjectSchema))


class ParameterObjectSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Regexp(RE_PARAMETER_NAME))
    in_ = fields.String(data_key='in', required=True, validate=validate.OneOf(PARAMETER_LOCATIONS))
    description = description
    required = required
    deprecated = deprecated
    schema = fields.Nested(SchemaObjectSchema)
    style = style
    example = example
    examples = fields.Dict(fields.String(required=True), fields.Nested(ExampleObjectSchema))
    content = fields.Dict(
        fields.String(required=True, validate=validate.OneOf(MEDIA_TYPES)),
        fields.Nested(MediaTypeObjectSchema, required=True),
    )

    @validates_schema
    def validate_required_field(self, data, **kwargs):
        if not data.get('required') and data['in_'] == 'path':
            raise ValidationError('Path parameter must be required!')


class OperationObjectSchema(BaseSchema):
    tags = fields.List(fields.String())
    summary = summary
    description = description
    externalDocs = fields.Nested(ExternalDocumentationObjectSchema)
    operationId = operation_id
    parameters = fields.Dict(fields.String(required=True), fields.Nested(ParameterObjectSchema))
    requestBody = fields.Nested(RequestBodyObjectSchema)
    responses = fields.Dict(
        fields.String(required=True, validate=validate.Regexp(RE_RESPONSE_STATUS_CODE)),
        fields.Nested(ResponseObjectSchema, required=True),
        required=True,
    )
    callbacks = fields.Dict(
        fields.String(required=True),
        fields.Dict(
            fields.String(required=True), fields.Nested('PathItemObjectSchema', required=True)
        ),
    )
    deprecated = deprecated
    security = fields.List(fields.Dict(fields.String(), fields.List(fields.String())))
    servers = fields.Nested(ServerObjectSchema, many=True)


class InfoObjectSchema(BaseSchema):
    title = fields.String(required=True)
    description = description
    termsOfService = fields.URL()
    contact = fields.Nested(ContactObjectSchema)
    license = fields.Nested(LicenseObjectSchema)
    version = fields.String(required=True)


class OAuthFlowsObjectSchema(BaseSchema):
    implicit = fields.Nested(OAuthFlowObjectSchema)
    password = fields.Nested(OAuthFlowObjectSchema)
    clientCredentials = fields.Nested(OAuthFlowObjectSchema)
    authorizationCode = fields.Nested(OAuthFlowObjectSchema)


class SecuritySchemeObjectSchema(BaseSchema):
    type_ = fields.String(data_key='type', required=True, validate=validate.OneOf(SECURITY_TYPES))
    description = description
    name = name
    in_ = fields.String(data_key='in', validate=validate.OneOf(['query', 'header', 'cookie']))
    scheme = fields.String(validate=validate.OneOf(['basic', 'bearer', 'digest', 'oauth']))
    bearerFormat = fields.String()
    flows = fields.Nested(OAuthFlowsObjectSchema)
    openIdConnectUrl = fields.URL()

    @validates_schema
    def validate_api_key(self, data, **kwargs):
        if data['type_'] == 'apiKey':
            if not data.get('name'):
                raise ValidationError('Parameter <name> required with type <apiKey>!')

            if not data.get('in_'):
                raise ValidationError('Parameter <in> required with type <apiKey>!')

    @validates_schema
    def validate_http(self, data, **kwargs):
        if data['type_'] == 'http':
            if not data.get('scheme'):
                raise ValidationError('Parameter <scheme> required with type <http>!')

            if data.get('scheme') == 'bearer':
                if not data.get('bearerFormat'):
                    raise ValidationError(
                        'Parameter <bearerFormat> required with type <http> and scheme <bearer>!'
                    )

    @validates_schema
    def validate_oauth(self, data, **kwargs):
        if data['type_'] == 'oauth':
            if not data.get('flows'):
                raise ValidationError('Parameter <flows> required with type <oauth>!')

    @validates_schema
    def validate_open_id_connect_url(self, data, **kwargs):
        if data['type_'] == 'openIdConnect':
            if not data.get('openIdConnectUrl'):
                raise ValidationError(
                    'Parameter <openIdConnectUrl> required with type <openIdConnect>!'
                )


class ComponentsObjectSchema(BaseSchema):
    schemas = fields.Dict(fields.String(required=True), fields.Nested(SchemaObjectSchema))
    responses = fields.Dict(fields.String(required=True), fields.Nested(ResponseObjectSchema))
    parameters = fields.Dict(fields.String(required=True), fields.Nested(ParameterObjectSchema))
    examples = fields.Dict(fields.String(required=True), fields.Nested(ExampleObjectSchema))
    requestBodies = fields.Dict(
        fields.String(required=True), fields.Nested(RequestBodyObjectSchema)
    )
    headers = fields.Dict(fields.String(required=True), fields.Nested(HeaderObjectSchema))
    securitySchemes = fields.Dict(
        fields.String(required=True), fields.Nested(SecuritySchemeObjectSchema)
    )
    links = fields.Dict(fields.String(required=True), fields.Nested(LinkObjectSchema))
    callbacks = fields.Dict(
        fields.String(required=True),
        fields.Dict(
            fields.String(required=True), fields.Nested('PathItemObjectSchema', required=True)
        ),
    )


class TagObjectSchema(BaseSchema):
    name = fields.String(required=True)
    description = description
    externalDocs = fields.Nested(ExternalDocumentationObjectSchema)


class PathItemObjectSchema(BaseSchema):
    summary = summary
    description = description
    get = fields.Nested(OperationObjectSchema)
    put = fields.Nested(OperationObjectSchema)
    post = fields.Nested(OperationObjectSchema)
    delete = fields.Nested(OperationObjectSchema)
    options = fields.Nested(OperationObjectSchema)
    head = fields.Nested(OperationObjectSchema)
    patch = fields.Nested(OperationObjectSchema)
    trace = fields.Nested(OperationObjectSchema)
    servers = fields.Nested(ServerObjectSchema, many=True)
    parameters = fields.Dict(fields.String(required=True), fields.Nested(ParameterObjectSchema))


class OpenAPIObjectSchema(BaseSchema):
    openapi = fields.String(required=True)
    info = fields.Nested(InfoObjectSchema, required=True)
    servers = fields.Nested(ServerObjectSchema, many=True)
    paths = fields.Dict(
        fields.String(required=True, validate=validate.Regexp(RE_ROUTE_PATH)),
        fields.Nested(PathItemObjectSchema, required=True),
        required=True,
    )
    components = fields.Nested(ComponentsObjectSchema)
    tags = fields.Nested(TagObjectSchema, many=True)
    externalDocs = fields.Nested(ExternalDocumentationObjectSchema)
