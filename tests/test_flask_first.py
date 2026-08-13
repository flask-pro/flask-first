from pathlib import Path

import pytest
from flask import Flask
from flask_first import First
from flask_first.exceptions import FirstException


def test_specification__factory_app(fx_get_path_spec_3_2_0):
    first = First(Path(fx_get_path_spec_3_2_0('mini.openapi.yaml')))

    def create_app():
        flask_app = Flask('factory_app')
        flask_app.debug = True
        flask_app.testing = True
        first.init_app(flask_app)
        return flask_app

    @first.route('/endpoint')
    def mini_endpoint() -> dict:
        return {'message': 'test_factory_app'}

    app = create_app()

    with app.test_client() as test_client:
        r = test_client.get('/endpoint')
        assert r.status_code == 200
        assert r.json['message'] == 'test_factory_app'


def test_specification__endpoint_registration(fx_get_path_spec_3_2_0):
    app = Flask('factory_app')
    app.debug = True
    app.testing = True

    first = First(Path(fx_get_path_spec_3_2_0('mini.openapi.yaml')), app=app)

    def mini_endpoint() -> dict:
        return {'message': 'test_factory_app'}

    first.endpoint_registration('/endpoint', mini_endpoint, methods=['GET'])

    with app.test_client() as test_client:
        r = test_client.get('/endpoint')
        assert r.status_code == 200
        assert r.json['message'] == 'test_factory_app'


def test_flask_first__no_spec_endpoint(fx_create_app, fx_get_path_spec_3_2_0):
    app = Flask('testing_app')
    app.debug = True
    app.testing = True
    app.config['FIRST_RESPONSE_VALIDATION'] = True

    path_to_spec = fx_get_path_spec_3_2_0('mini.openapi.yaml')
    first = First(path_to_spec, swagger_ui_path='/docs')

    first.init_app(app)

    @first.route('/endpoint')
    def endpoint() -> dict:
        return {'field': 'OK'}

    @app.route('/no_spec')
    def no_spec_endpoint() -> str:
        return 'OK'

    r = app.test_client().get('/endpoint')
    assert r.json == {'field': 'OK'}

    r = app.test_client().get('/no_spec')
    assert r.text == 'OK'


def test_flask_first__one_endpoint_several_methods(fx_create_app, fx_get_path_spec_3_2_0):
    app = Flask('testing_app')
    app.debug = True
    app.testing = True
    app.config['FIRST_RESPONSE_VALIDATION'] = True

    path_to_spec = fx_get_path_spec_3_2_0('several_methods.openapi.yaml')
    first = First(path_to_spec, app=app)

    @first.route('/endpoint', methods=['POST'])
    def post_endpoint() -> dict:
        return {'method': 'POST'}

    @first.route('/endpoint')
    def get_endpoint() -> dict:
        return {'method': 'GET'}

    r = app.test_client().post('/endpoint')
    assert r.json == {'method': 'POST'}

    r = app.test_client().get('/endpoint')
    assert r.json == {'method': 'GET'}


def test_flask_first__double_endpoint_error(fx_create_app, fx_get_path_spec_3_2_0):
    app = Flask('testing_app')
    app.debug = True
    app.testing = True

    path_to_spec = fx_get_path_spec_3_2_0('several_methods.openapi.yaml')
    first = First(path_to_spec, app=app)

    rule = '/endpoint'

    @first.route(rule)
    def post_endpoint() -> dict:
        return {'method': 'First endpoint'}

    with pytest.raises(FirstException) as exc:

        @first.route(rule)
        def get_endpoint() -> dict:
            return {'method': 'Second endpoint'}

    assert exc.value.args[0] == 'Rule </endpoint> exits.'


def test_flask_first__route_not_in_spec(fx_create_app, fx_get_path_spec_3_2_0):
    app = Flask('testing_app')
    app.debug = True
    app.testing = True

    path_to_spec = fx_get_path_spec_3_2_0('several_methods.openapi.yaml')
    first = First(path_to_spec, app=app)

    with pytest.raises(FirstException) as exc:

        @first.route('/not_in_spec', methods=['PATCH'])
        def get_endpoint() -> dict:
            return {'method': 'Second endpoint'}

    assert exc.value.args[0] == 'Route </not_in_spec> not exist in OpenAPI specification.'


def test_flask_first__method_not_in_spec(fx_create_app, fx_get_path_spec_3_2_0):
    app = Flask('testing_app')
    app.debug = True
    app.testing = True

    path_to_spec = fx_get_path_spec_3_2_0('several_methods.openapi.yaml')
    first = First(path_to_spec, app=app)

    with pytest.raises(FirstException) as exc:

        @first.route('/endpoint', methods=['PATCH'])
        def get_endpoint() -> dict:
            return {'method': 'Second endpoint'}

    assert (
        exc.value.args[0]
        == 'Route </endpoint> for method <PATCH> not exist in OpenAPI specification.'
    )
