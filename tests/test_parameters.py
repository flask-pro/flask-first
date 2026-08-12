from flask import Flask
from flask import request
from flask_first import First


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


def test_parameters_as_root(fx_get_path_spec_3_2_0, fx_create_app):
    app = Flask(__name__)
    app.config['FIRST_RESPONSE_VALIDATION'] = True

    path_to_spec = fx_get_path_spec_3_2_0('parameters/root_path_param.openapi.yaml')
    first = First(path_to_spec, app=app, swagger_ui_path='/docs')

    @first.route('/{path_param}')
    def endpoint(path_param) -> dict:
        assert request.extensions['first']['paths']['path_param'] == path_param
        return request.extensions['first']['paths']

    r = app.test_client().get('/test_root_path_param')
    assert r.status_code == 200
    assert r.json == {'path_param': 'test_root_path_param'}
