from flask import request


def test_request_body(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        return {'field': request.json['field']}

    path_to_spec = fx_get_path_spec_3_2_0('request_body/mini.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['POST'])

    r = test_client.post(path, json={'field': 'OK'})
    assert r.status_code == 200
    assert r.json['field'] == 'OK'
