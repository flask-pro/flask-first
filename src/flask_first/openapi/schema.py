from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import conint
from pydantic import constr
from pydantic import EmailStr
from pydantic import Field
from pydantic import HttpUrl
from pydantic import root_validator
from pydantic import validator
from typing import Optional


class ServerVariableObject(BaseModel):
    enum: list[str] | None
    default: str
    description: str | None


class ServerObject(BaseModel):
    url: HttpUrl
    description: str | None
    variables: dict[str, ServerVariableObject]


class ReferenceObject(BaseModel):
    ref_: str = Field(alias='$ref', regex=r'#/components/(schemas|parameters)/[a-zA-Z0-9\-_]')


class ExternalDocumentationObject(BaseModel):
    description: str | None
    url: HttpUrl


class LocationsParameter(str, Enum):
    QUERY = 'query'
    HEADER = 'header'
    PATH = 'path'
    COOKIE = 'cookie'


class ParameterObject(BaseModel):
    name: str
    in_: LocationsParameter = Field(alias='in')
    description: str | None
    required: bool | None
    deprecated: bool | None
    allowEmptyValue: bool | None

    @root_validator
    def required_validation(cls, values) -> [dict, ValueError]:
        in_ = values['in_']
        if in_ == LocationsParameter.PATH and values['required'] is True:
            return values
        else:
            raise ValueError('If <in> is <path> then <required> must be <true>.')

    @root_validator
    def name_validation(cls, values):
        raise NotImplementedError


class DiscriminatorObject(BaseModel):
    propertyName: str
    mapping: dict[str, str] | None


class XMLObject(BaseModel):
    name: str | None
    namespace: str | None
    prefix: str | None
    attribute: bool | None
    wrapped: bool | None


class SchemaObject(BaseModel):
    title: str | None
    multipleOf: int | None
    maximum: int | None
    exclusiveMaximum: bool | None
    minimum: int | None
    exclusiveMinimum: bool | None
    maxLength: conint(ge=0) | None
    minLength: conint(ge=0) | None
    pattern: str | None
    maxItems: conint(ge=0) | None
    minItems: conint(ge=0) | None
    uniqueItems: bool | None
    maxProperties: conint(ge=0) | None
    minProperties: conint(ge=0) | None
    required: list[str] | None
    enum: list[Any]
    type: str
    allOf: Optional['SchemaObject'] | None
    oneOf: Optional['SchemaObject'] | None
    anyOf: Optional['SchemaObject'] | None
    not_: Optional['SchemaObject'] | None = Field(alias='not')
    items: Optional['SchemaObject'] | None
    properties: Optional['SchemaObject'] | None
    additionalProperties: bool | None
    description: str | None
    format: str | None
    default: Any | None
    nullable: bool | None
    discriminator: DiscriminatorObject | None
    readOnly: bool | None
    writeOnly: bool | None
    xml: XMLObject | None
    externalDocs: ExternalDocumentationObject | None
    example: Any | None
    deprecated: bool

    @validator('multipleOf')
    def multiple_of_validation(cls, value):
        raise NotImplementedError

    @validator('type')
    def type_validation(cls, value):
        raise NotImplementedError

    @validator('format')
    def format_validation(cls, value):
        raise NotImplementedError

    @root_validator
    def maximum_validation(cls, values):
        raise NotImplementedError

    @root_validator
    def minimum_validation(cls, values):
        raise NotImplementedError

    @root_validator
    def required_validation(cls, values):
        raise NotImplementedError

    @root_validator
    def default_validation(cls, values):
        raise NotImplementedError


class ExampleObject(BaseModel):
    summary: str | None
    description: str | None
    value: Any | None
    externalValue: str | None

    @validator('value')
    def value_validation(cls, value):
        raise NotImplementedError

    @validator('externalValue')
    def externalValue_validation(cls, value):
        raise NotImplementedError



class EncodingObject(BaseModel):
    raise NotImplementedError


class MediaTypeObject(BaseModel):
    schema: SchemaObject | ReferenceObject | None
    example: Any
    examples: dict[str, ExampleObject | ReferenceObject]
    encoding: dict[str, EncodingObject]


class RequestBodyObject(BaseModel):
    description: str | None
    content: dict[str, MediaTypeObject]
    required: bool | None


class OAuthFlowObject(BaseModel):
    authorizationUrl: str | None
    tokenUrl: str | None
    refreshUrl: str | None
    scopes: dict[str, str] | None

    @validator('authorizationUrl')
    def authorization_url_validation(cls, value):
        raise NotImplementedError

    @validator('tokenUrl')
    def token_url_validation(cls, value):
        raise NotImplementedError

    @validator('scopes')
    def scopes_validation(cls, value):
        raise NotImplementedError


class OAuthFlowsObject(BaseModel):
    implicit: OAuthFlowObject | None
    password: OAuthFlowObject | None
    clientCredentials: OAuthFlowObject | None
    authorizationCode: OAuthFlowObject | None


class SecurityRequirementObject(BaseModel):
    type: constr(regex=r'^(apiKey|http|oauth2|openIdConnect)$')
    description: str | None
    name: str | None
    in_: LocationsParameter = Field(alias='in')
    scheme: str | None
    bearerFormat: str | None
    flows: OAuthFlowsObject | None
    openIdConnectUrl: str | None

    @validator('name')
    def name_validation(cls, value):
        raise NotImplementedError

    @validator('in')
    def in_validation(cls, value):
        raise NotImplementedError

    @validator('scheme')
    def scheme_validation(cls, value):
        raise NotImplementedError

    @validator('flows')
    def flows_validation(cls, value):
        raise NotImplementedError

    @validator('openIdConnectUrl')
    def flows_validation(cls, value):
        raise NotImplementedError


class CallbackObject(BaseModel):
    raise NotImplementedError


class ResponsesObject(BaseModel):
    raise NotImplementedError


class OperationObject(BaseModel):
    tags: list[str] | None
    summary: str | None
    description: str | None
    externalDocs: ExternalDocumentationObject | None
    operationId: str | None
    parameters: list[ParameterObject | ReferenceObject] | None
    requestBody: RequestBodyObject | ReferenceObject | None
    responses: ResponsesObject
    callbacks: dict[str, CallbackObject | ReferenceObject] | None
    deprecated: bool | None
    security: list[SecurityRequirementObject] | None
    servers: list[ServerObject] | None


class PathItemObject(BaseModel):
    ref_: str | None = Field(alias='$ref')
    summary: str | None
    description: str | None
    get: OperationObject | None
    put: OperationObject | None
    post: OperationObject | None
    delete: OperationObject | None
    options: OperationObject | None
    head: OperationObject | None
    patch: OperationObject | None
    trace: OperationObject | None
    servers: list[ServerObject]
    parameters: list[ParameterObject | ReferenceObject]


class Route(BaseModel):
    __root__: constr(regex=r'^/[a-z\-{}_/]*$')


class PathsObject(BaseModel):
    __root__: dict[Route, PathItemObject]


class LicenseObject(BaseModel):
    name: str
    url: HttpUrl | None


class ContactObject(BaseModel):
    name: str | None
    url: HttpUrl | None
    email: EmailStr | None


class InfoObject(BaseModel):
    title: str
    description: str
    termsOfService: str
    contact: ContactObject
    license: LicenseObject
    version: constr(regex=r'^\d.\d.\d$')


class LinkObject(BaseModel):
    raise NotImplementedError


class SecuritySchemeObject(BaseModel):
    raise NotImplementedError


class HeaderObject(BaseModel):
    raise NotImplementedError


class ResponseObject(BaseModel):
    raise NotImplementedError


class ComponentsObject(BaseModel):
    schemas: dict[str, SchemaObject | ReferenceObject] | None
    responses: dict[str, ResponseObject | ReferenceObject] | None
    parameters: dict[str, ParameterObject | ReferenceObject] | None
    examples: dict[str, ExampleObject | ReferenceObject] | None
    requestBodies: dict[str, RequestBodyObject | ReferenceObject] | None
    headers: dict[str, HeaderObject | ReferenceObject] | None
    securitySchemes: dict[str, SecuritySchemeObject | ReferenceObject] | None
    links: dict[str, LinkObject | ReferenceObject] | None
    callbacks: dict[str, CallbackObject | ReferenceObject] | None


class TagObject(BaseModel):
    name: str
    description: str | None
    externalDocs: ExternalDocumentationObject | None


class OpenAPIObject(BaseModel):
    openapi: constr(regex=r'^3.0.3$')
    info: InfoObject
    servers: list[ServerObject] | None
    paths: PathsObject
    components: ComponentsObject | None
    security: list[SecurityRequirementObject] | None
    tags: TagObject | None
    externalDocs: ExternalDocumentationObject | None


class OpenAPI303(BaseModel):
    """Root model for OpenAPI v.3.0.3."""

    __root__: OpenAPIObject
