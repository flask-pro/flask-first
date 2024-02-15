from pathlib import Path

from flask import request

from .conftest import BASEDIR


def test_responses__default(fx_create_app):
    def default_responses() -> dict:
        return {'message': request.json['message']}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.1.0/responses.default.openapi.yaml'), [default_responses]
    )

    r = test_client.post('/message', json={'message': 'OK'})
    assert r.status_code == 200
    assert r.json['message'] == 'OK'
