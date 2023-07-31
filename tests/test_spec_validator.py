from pathlib import Path

import pytest
from flask import Flask
from flask_first import First

from .conftest import BASEDIR


@pytest.mark.parametrize(
    'spec',
    Path(BASEDIR, 'specs/valid').iterdir(),
    ids=[file.name for file in Path(BASEDIR, 'specs/valid').iterdir()],
)
def test_spec_validator(spec):
    app = Flask('check_v30_specs')
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    first = First(spec, app=app, swagger_ui_path='/docs')

    def get_endpoint() -> dict:
        return {'message': 'OK'}

    first.add_view_func(get_endpoint)

    app.test_client().set_cookie('Test-Cookie')

    r = app.test_client().get('/get_endpoint', follow_redirects=True)
    assert r.status_code == 200
    assert r.json['message'] == 'OK'
