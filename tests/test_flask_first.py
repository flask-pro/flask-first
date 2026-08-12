from pathlib import Path

from flask import Flask
from flask_first import First


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

    first.endpoint_registration('/endpoint', mini_endpoint)

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
        return {'message': 'OK'}

    @app.route('/no_spec')
    def no_spec_endpoint() -> str:
        return 'OK'

    r = app.test_client().get('/no_spec')
    assert r.text == 'OK'
