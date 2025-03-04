from collections.abc import Iterable
from pathlib import Path

import pytest
import yaml
from flask import Flask
from flask_first import First
from openapi_spec_validator import validate as osv_validate
from openapi_spec_validator.readers import read_from_filename


@pytest.fixture
def fx_spec_minimal():
    payload = {
        'openapi': '3.1.1',
        'info': {'title': 'API for testing Flask-First', 'version': '1.0.0'},
        'paths': {
            '/endpoint': {
                'get': {
                    'operationId': 'endpoint',
                    'responses': {
                        '200': {
                            'description': 'OK',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {'message': {'type': 'string'}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    return payload


@pytest.fixture
def fx_spec_as_file(tmp_path):
    def create(spec: dict, validate: bool = True, file_name: str = 'openapi.yaml') -> Path:
        spec_path = Path(tmp_path, file_name)
        with open(spec_path, 'w+') as f:
            yaml.dump(spec, f)

        spec_as_dict, _ = read_from_filename(str(spec_path))
        if validate:
            osv_validate(spec_as_dict)

        return spec_path

    return create


@pytest.fixture()
def fx_create_app():
    def _create_app(path_to_spec: str, routes_functions: Iterable):
        app = Flask('testing_app')
        app.debug = True
        app.config['FIRST_RESPONSE_VALIDATION'] = True
        app.config['FIRST_DATETIME_FORMAT'] = "%Y-%m-%dT%H:%M:%S.%fZ"

        first = First(path_to_spec, app, swagger_ui_path='/docs')
        for func in routes_functions:
            first.add_view_func(func)

        app_context = app.app_context()
        app_context.push()

        with app.test_client() as test_client:
            return test_client

    return _create_app
