from flask import request


def test_parameters_from_path(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint(path_param_1, path_param_2) -> dict:
        assert request.extensions['first']['paths']['path_param_1'] == path_param_1
        assert request.extensions['first']['paths']['path_param_2'] == path_param_2

        return request.extensions['first']['paths']

    path_to_spec = fx_get_path_spec_3_2_0('parameters/path_parameters.openapi.yaml')
    path = '/endpoint/{path_param_1}/{path_param_2}'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['GET'])

    r = test_client.get('/endpoint/value_1/value_2')
    assert r.status_code == 200
    assert r.json == {'path_param_1': 'value_1', 'path_param_2': 'value_2'}


def test_parameters_from_query(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        return request.extensions['first']['queries']

    path_to_spec = fx_get_path_spec_3_2_0('parameters/query_parameters.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['GET'])

    query_string = {'query_param_1': 'value_1'}
    r = test_client.get(path, query_string=query_string)
    assert r.status_code == 200
    assert r.json == query_string
