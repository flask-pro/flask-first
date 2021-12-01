import os

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.flask_first import First

basedir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture()
def fx_config():
    class Config:
        PATH_TO_SPEC = os.path.join(basedir, "specs/v3.0/openapi.yaml")

    return Config


@pytest.fixture()
def fx_app(fx_config):
    app = Flask("testing_app")
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
