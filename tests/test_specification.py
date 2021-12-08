import os
from pathlib import Path

import pytest
from flask import Flask
from flask import request

from src.flask_first import First
from src.flask_first import Specification


def test_specification__load_from_yaml(fx_config):
    spec = Specification(fx_config.PATH_TO_SPEC)
    assert spec
    assert spec.serialized['info']['title'] == 'Simple API for testing Flask-First'


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
    full_spec = Path('specs/v3.0/full.openapi.yaml')
    First(full_spec, app)


@pytest.mark.parametrize('spec', os.listdir('specs/v3.0'))
def test_specification__check_v30_specs(spec):
    specs_dir = 'specs/v3.0'
    app = Flask('check_v30_specs')
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(f'{specs_dir}/{spec}')
    First(full_spec, app=app, swagger_ui_path='/docs')

    r = app.test_client().get('/docs', follow_redirects=True)
    assert r.status_code == 200
    assert '/docs/openapi.yaml' in r.data.decode()


def test_specification__nullable_parameter():
    app = Flask('testing_app')
    app.debug = True
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path('specs/v3.0/nullable.openapi.yaml')
    first = First(full_spec, app)

    def nullable_endpoint() -> dict:
        return {'message': request.json['message']}

    first.add_view_func(nullable_endpoint)

    r = app.test_client().post('/nullable_endpoint', json={'message': None})
    assert r.status_code == 200
    assert r.json == {'message': None}
