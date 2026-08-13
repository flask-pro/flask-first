from typing import Any

from flask import Request
from flask import Response
from marshmallow import fields
from schema_first import Specification
from werkzeug.routing import Rule


class RequestAdapter:

    def __init__(self, request: Request, map_rules_to_paths: dict, spec: Specification) -> None:
        self.request = request
        self.map_rules_to_paths = map_rules_to_paths
        self.spec = spec

        self.method = self.request.method.lower()
        self.endpoint = self._get_endpoint()
        self.headers = dict(self.request.headers)
        self.cookies = self.request.cookies
        self.paths = self.request.view_args
        self.queries = self._serialize_args(self.request.args)
        self.content_type = self.request.mimetype
        self.body = self.request.get_json() if self.request.is_json else self.request.data

    def _get_endpoint(self) -> str | Rule | None | Any:
        if self.request.url_rule is not None:
            rule = self.request.url_rule.rule
        elif self.request.url_rule is str:
            rule = self.request.url_rule
        else:
            rule = self.request.path

        endpoint = self.map_rules_to_paths.get(rule)
        if endpoint:
            return endpoint

        return rule

    def _serialize_args(self, raw_args) -> dict[str, Any]:
        serialized_args = {}

        raw_args = self.request.args.to_dict(flat=False)
        if not raw_args:
            return serialized_args

        paths = self.spec.reassembly_spec['paths']
        path_from_spec = self.map_rules_to_paths[self.request.url_rule.rule]
        params_schemas = paths[path_from_spec][self.method].get('parameters')
        if params_schemas:
            args_schema = params_schemas.get('queries')
            if args_schema:
                schema_of_args = args_schema['schema']()
                for name, value in raw_args.items():
                    arg_field_from_schema = schema_of_args.fields.get(name)
                    if arg_field_from_schema is None:
                        serialized_args[name] = value
                    elif isinstance(schema_of_args.fields[name], fields.List):
                        serialized_args[name] = value
                    else:
                        serialized_args[name] = value[0]
        else:
            serialized_args = raw_args

        return serialized_args

    def to_dict(self):
        request_as_dict = {'method': self.method, 'endpoint': self.endpoint}

        if self.headers:
            request_as_dict['headers'] = self.headers

        if self.cookies:
            request_as_dict['cookies'] = self.cookies

        if self.paths:
            request_as_dict['paths'] = self.paths

        if self.queries:
            request_as_dict['queries'] = self.queries

        if self.content_type:
            request_as_dict['content_type'] = self.content_type

        if self.body:
            request_as_dict['body'] = self.body

        return request_as_dict


class ResponseAdapter:

    def __init__(
        self, request: Request, response: Response, map_rules_to_paths: dict, spec: Specification
    ) -> None:
        self.request = request
        self.response = response
        self.map_rules_to_paths = map_rules_to_paths
        self.spec = spec

        self.request_adapter = RequestAdapter(self.request, self.map_rules_to_paths, self.spec)

        self.headers = dict(self.response.headers)
        self.status_code = str(self.response.status_code)
        self.content_type = self.response.mimetype
        self.body = self.response.get_json() if self.response.is_json else self.response.data

    def to_dict(self):
        response_as_dict = {
            k: v for k, v in self.request_adapter.to_dict().items() if k in ('endpoint', 'method')
        }

        if self.status_code:
            response_as_dict['status_code'] = self.status_code

        if self.content_type:
            response_as_dict['content_type'] = self.content_type

        if self.body:
            response_as_dict['body'] = self.body

        return response_as_dict
