import os
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_first import First

BASEDIR = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture()
def fx_config():
    class Config:
        PATH_TO_SPEC = Path(BASEDIR, 'specs/v3.0/openapi.yaml')

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
    def _create_app(path_to_spec: str, routes_functions: tuple):
        app = Flask('testing_app')
        app.debug = 1
        app.config['FIRST_RESPONSE_VALIDATION'] = True

        first = First(path_to_spec, app)
        for func in routes_functions:
            first.add_view_func(func)

        app_context = app.app_context()
        app_context.push()

        with app.test_client() as test_client:
            return test_client

    return _create_app
