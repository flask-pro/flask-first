import re

from marshmallow import EXCLUDE
from marshmallow.exceptions import ValidationError

from .exceptions import FirstEndpointValidation
from .exceptions import FirstRequestArgsValidation
from .exceptions import FirstRequestCookiesValidation
from .exceptions import FirstRequestHeadersValidation
from .exceptions import FirstRequestJSONValidation
from .exceptions import FirstRequestPathArgsValidation
from .specification import Specification


class RequestSerializer:
    RE_ENDPOINT = r'^/[\w/{}-]*$'
    DEFAULT_CONTENT_TYPE = 'application/json'

    def __init__(
        self,
        spec: Specification,
        method: str,
        endpoint: str,
        headers: dict = None,
        cookies: dict = None,
        path_params: dict = None,
        params: dict = None,
        json: dict = None,
    ) -> None:
        self.spec = spec
        self._paths_schema = self.spec.serialized_spec['paths']

        self.method = method.lower()
        self.endpoint = endpoint
        self.headers = headers
        self.cookies = cookies
        self.path_params = path_params
        self.params = params
        self.json = json

        self.serialized_method = method.lower()
        self.serialized_endpoint = endpoint.lower()
        self.serialized_headers = headers
        self.serialized_cookies = cookies
        self.serialized_path_params = path_params
        self.serialized_params = params
        self.serialized_json = json

    def _validating_endpoint(self) -> [None | Exception]:
        endpoint = re.fullmatch(self.RE_ENDPOINT, self.endpoint)
        if endpoint is None:
            raise FirstEndpointValidation(
                f'Endpoint <{self.endpoint}> not validating via regex <{self.RE_ENDPOINT}>.'
            )
        elif self.endpoint not in self._paths_schema:
            raise FirstEndpointValidation(
                f'Endpoint <{self.endpoint}> not in OpenAPI specification.'
            )

    def _validating_method(self) -> [None | Exception]:
        if self.method not in self._paths_schema[self.endpoint]:
            raise FirstEndpointValidation(
                f'Endpoint <{self.endpoint}> not in OpenAPI specification.'
            )

    def _validating_headers(self) -> [None | Exception]:
        params_schemas = self._paths_schema[self.endpoint][self.method].get('parameters')
        if params_schemas:
            headers_schema = params_schemas.get('headers')
            if headers_schema:
                try:
                    self.serialized_headers = headers_schema(unknown=EXCLUDE).load(self.headers)
                except ValidationError as e:
                    raise FirstRequestHeadersValidation(str(e))
        else:
            if self.path_params:
                raise FirstRequestHeadersValidation('Headers of request not in specification.')

    def _validating_cookies(self) -> [None | Exception]:
        params_schemas = self._paths_schema[self.endpoint][self.method].get('parameters')
        if params_schemas:
            cookies_schema = params_schemas.get('cookies')
            if cookies_schema:
                try:
                    self.serialized_cookies = cookies_schema(unknown=EXCLUDE).load(self.headers)
                except ValidationError as e:
                    raise FirstRequestCookiesValidation(str(e))
        else:
            if self.path_params:
                raise FirstRequestCookiesValidation('Cookies of request not in specification.')

    def _validating_path_params(self) -> [None | Exception]:
        params_schemas = self._paths_schema[self.endpoint][self.method].get('parameters')
        if params_schemas:
            path_params_schema = params_schemas.get('view_args')
            if path_params_schema:
                try:
                    self.serialized_path_params = path_params_schema().load(self.path_params)
                except ValidationError as e:
                    raise FirstRequestPathArgsValidation(str(e))
        else:
            if self.path_params:
                raise FirstRequestPathArgsValidation(
                    'Path parameters of request not in specification.'
                )

    def _validating_params(self) -> [None | Exception]:
        params_schemas = self._paths_schema[self.endpoint][self.method].get('parameters')
        if params_schemas:
            args_schema = params_schemas.get('args')
            if args_schema:
                try:
                    self.serialized_params = args_schema().load(self.params)
                except ValidationError as e:
                    raise FirstRequestArgsValidation(str(e))
        else:
            if self.params:
                raise FirstRequestArgsValidation('Parameters of request not in specification.')

    def _validating_json(self) -> [None | Exception]:
        request_body = self._paths_schema[self.endpoint][self.method].get('requestBody')
        if request_body:
            content = self._paths_schema[self.endpoint][self.method]['requestBody']['content']
            json_schema = content[self.DEFAULT_CONTENT_TYPE]['schema']
            try:
                if isinstance(self.json, list):
                    self.serialized_json = json_schema._load(self.json, None)
                elif 'allOf' in json_schema._declared_fields:
                    self.serialized_json = json_schema().load({'allOf': self.json})
                elif 'anyOf' in json_schema._declared_fields:
                    self.serialized_json = json_schema().load({'anyOf': self.json})
                elif 'oneOf' in json_schema._declared_fields:
                    self.serialized_json = json_schema().load({'oneOf': self.json})
                else:
                    self.serialized_json = json_schema().load(self.json)
            except ValidationError as e:
                raise FirstRequestJSONValidation(str(e))
        else:
            if self.json:
                raise FirstRequestJSONValidation('JSON of request not in specification.')

    def validate(self):
        self._validating_endpoint()
        self._validating_method()
        self._validating_headers()
        self._validating_cookies()
        self._validating_path_params()
        self._validating_params()
        self._validating_json()
