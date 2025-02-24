import os
from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from flask import Flask
from flask.testing import FlaskClient
from flask_first import First

BASEDIR = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture()
def fx_config():
    class Config:
        PATH_TO_SPEC = Path(BASEDIR, 'specs/v3.1.0/openapi.yaml')

    return Config


@pytest.fixture()
def fx_app(fx_config):
    app = Flask('testing_app')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    First(fx_config.PATH_TO_SPEC, app)

    app_context = app.app_context()
    app_context.push()

    yield app

    # Stop app for testing.
    app_context.pop()


@pytest.fixture()
def fx_client(fx_app) -> FlaskClient:
    with fx_app.test_client() as test_client:
        return test_client


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


@pytest.fixture
def fx_make_minimal_spec() -> dict:
    return {
        'openapi': '3.1.0',
        'info': {'title': 'API for testing Flask-First', 'version': '1.0.0'},
        'paths': {
            '/endpoint': {
                'get': {
                    'operationId': 'get_endpoint',
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
                },
                'post': {
                    'operationId': 'post_endpoint',
                    'requestBody': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {'message': {'type': 'string'}},
                                }
                            }
                        }
                    },
                    'responses': {
                        '201': {
                            'description': 'OK',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {'message': {'type': 'string'}},
                                    }
                                }
                            },
                        },
                        'default': {
                            'description': 'OK',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {'message': {'type': 'string'}},
                                    }
                                }
                            },
                        },
                    },
                },
            }
        },
    }


@pytest.fixture
def fx_make_spec_file(tmp_path, fx_make_minimal_spec):
    def _make_spec(paths: dict = None, url: str = None, parameters: list = None) -> Path:
        spec = deepcopy(fx_make_minimal_spec)

        if paths:
            spec['paths'] = paths
        if parameters:
            spec['paths']['/endpoint']['parameters'] = parameters
        if url:
            spec['paths'][url] = deepcopy(spec['paths']['/endpoint'])
            spec['paths'].pop('/endpoint')

        spec_file_path = tmp_path / 'openapi.yaml'
        with open(spec_file_path, 'w') as file:
            yaml.dump(spec, file)

        return spec_file_path

    return _make_spec
