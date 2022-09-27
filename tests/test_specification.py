from pathlib import Path

import pytest
from flask import Flask
from flask import request
from flask_first import First
from flask_first.exceptions import FirstOpenAPIValidation

from .conftest import BASEDIR


def test_specification__bad_response(fx_app, fx_client):
    def bad_response() -> dict:
        return {'message': 'OK', 'non_exist_field': 'BAD'}

    fx_app.extensions['first'].add_view_func(bad_response)

    fx_app.debug = 0
    fx_app.testing = 0

    assert fx_client.get('/bad_response').status_code == 500


def test_specification__full_field_openapi():
    app = Flask('testing_app')
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.0/full.openapi.yaml')
    First(full_spec, app)


def test_specification__bad_openapi():
    app = Flask('bad_api')
    app.debug = True
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/bad.openapi.yaml')
    try:
        assert not First(full_spec, app)
    except FirstOpenAPIValidation:
        assert True


@pytest.mark.parametrize('spec', Path(BASEDIR, 'specs/v3.0').iterdir())
def test_specification__check_v30_specs(spec):
    specs_dir = 'specs/v3.0'
    app = Flask('check_v30_specs')
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, specs_dir, spec)
    First(full_spec, app=app, swagger_ui_path='/docs')

    r = app.test_client().get('/docs', follow_redirects=True)
    assert r.status_code == 200
    assert '/docs/openapi.yaml' in r.data.decode()


def test_specification__nullable_parameter():
    app = Flask('testing_app')
    app.debug = True
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.0/nullable.openapi.yaml')
    first = First(full_spec, app)

    def nullable_endpoint() -> dict:
        return {'message': request.json['message']}

    first.add_view_func(nullable_endpoint)

    r = app.test_client().post('/nullable_endpoint', json={'message': None})
    assert r.status_code == 200, r.json
    assert r.json == {'message': None}
