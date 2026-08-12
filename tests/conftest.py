import os
import typing as t
from pathlib import Path

import pytest
from flask import Flask
from flask.testing import Client
from flask_first import First

BASEDIR = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def fx_get_path_spec_3_2_0():
    def _make_path(file_name: str):
        return Path(BASEDIR, 'specs', 'openapi', 'v3.2.0', file_name)

    return _make_path


@pytest.fixture
def fx_create_app():
    def _create_app(
        path_to_spec: str,
        func: t.Callable,
        path: str,
        methods: list[t.Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']] | None = None,
    ) -> Client:
        if methods is None:
            methods = ['GET']

        app = Flask('testing_app')
        app.debug = True
        app.testing = True
        app.config['FIRST_RESPONSE_VALIDATION'] = True

        first = First(path_to_spec, swagger_ui_path='/docs')

        @first.route(path, methods=methods)
        def endpoint(*args, **kwargs) -> dict:
            return func(*args, **kwargs)

        first.init_app(app)

        app_context = app.app_context()
        app_context.push()

        with app.test_client() as test_client:
            return test_client

    return _create_app
