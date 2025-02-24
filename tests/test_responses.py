from datetime import datetime
from pathlib import Path

import pytest
from flask import request
from flask_first.first.exceptions import FirstRequestJSONValidation
from flask_first.first.exceptions import FirstResponseJSONValidation

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


def test_responses__datetime(fx_create_app):
    def create_datetime() -> dict:
        datetime = request.extensions['first']['json']['datetime'].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return {'datetime': datetime}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.1.0/datetime.openapi.yaml'), [create_datetime]
    )

    json = {'datetime': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
    r = test_client.post('/datetime', json=json)
    assert r.status_code == 200
    assert r.json['datetime'] == json['datetime']


def test_responses__request_datetime_error(fx_create_app):
    def create_datetime() -> dict:
        datetime = request.extensions['first']['json']['datetime']
        return {'datetime': datetime}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.1.0/datetime.openapi.yaml'), [create_datetime]
    )

    json = {'datetime': datetime.utcnow().isoformat()}

    with pytest.raises(FirstRequestJSONValidation):
        test_client.post('/datetime', json=json)


def test_responses__response_datetime_error(fx_create_app):
    def create_datetime() -> dict:
        datetime = request.extensions['first']['json']['datetime'].isoformat()
        return {'datetime': datetime}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.1.0/datetime.openapi.yaml'), [create_datetime]
    )

    json = {'datetime': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")}

    with pytest.raises(FirstResponseJSONValidation):
        test_client.post('/datetime', json=json)
