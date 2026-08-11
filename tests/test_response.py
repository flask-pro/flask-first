import pytest
from flask import request
from schema_first.query.exceptions import ResponseValidation


def test_response(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        return {'field': request.json['field']}

    path_to_spec = fx_get_path_spec_3_2_0('request_body/mini.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['POST'])

    r = test_client.post(path, json={'field': 'OK'})
    assert r.status_code == 200
    assert r.json['field'] == 'OK'


def test_response_error(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        return {'field': 1}

    path_to_spec = fx_get_path_spec_3_2_0('request_body/mini.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['POST'])

    with pytest.raises(ResponseValidation) as exc:
        test_client.post(path, json={'field': 'OK'})
    assert (
        exc.value.args[0] == "Response <{'endpoint': '/endpoint', 'method': 'post',"
        " 'content_type': 'application/json', 'status_code': '200',"
        " 'body': {'field': 1}}> validation error"
        " <({'body': {'field': ['Not a valid string.']}},)>."
    )
