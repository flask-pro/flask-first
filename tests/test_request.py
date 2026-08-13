import pytest
from flask import request
from flask_first.exceptions import FirstRequestValidationError


def test_request(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        return {'field': request.json['field']}

    path_to_spec = fx_get_path_spec_3_2_0('request_body/mini.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['POST'])

    r = test_client.post(path, json={'field': 'OK'})
    assert r.status_code == 200
    assert r.json['field'] == 'OK'


def test_request_error(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        return {'field': request.json['field']}

    path_to_spec = fx_get_path_spec_3_2_0('request_body/mini.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['POST'])

    with pytest.raises(FirstRequestValidationError) as exc:
        test_client.post(path, json={'field': 1})

    assert exc.value.args[0] == (
        "Request <{'endpoint': '/endpoint', 'method': 'post', 'content_type': "
        "'application/json', 'headers': {'User-Agent': 'Werkzeug/3.1.8', 'Host': "
        "'localhost', 'Content-Type': 'application/json', 'Content-Length': '12'}, "
        "'body': {'field': 1}}> validation error <({'body': {'field': ['Not a valid "
        "string.']}},)>."
    )
