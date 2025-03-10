import uuid
from pathlib import Path

import pytest
from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
from flask_first import First
from flask_first.first.exceptions import FirstRequestPathArgsValidation

from .conftest import BASEDIR

ITEM = {
    'uuid': '789d995f-3aa0-4bf8-a37b-2f2f2086d503',
    'name': 'test_item',
    'description': 'Item from tests.',
}


def test_specification__factory_app():
    def mini_endpoint() -> dict:
        return {'message': 'test_factory_app'}

    first = First(Path(BASEDIR, 'specs/v3.1.0/mini.openapi.yaml'))

    def create_app():
        flask_app = Flask('factory_app')
        first.init_app(flask_app)
        first.add_view_func(mini_endpoint)
        return flask_app

    app = create_app()

    with app.test_client() as test_client:
        r = test_client.get('/mini_endpoint')
        assert r.status_code == 200
        assert r.json['message'] == 'test_factory_app'


def test_flask_first__swagger_ui(fx_create_app):
    def mini_endpoint() -> dict:
        return {'message': 'test_flask_first__swagger_ui'}

    test_client = fx_create_app(Path(BASEDIR, 'specs/v3.1.0/mini.openapi.yaml'), [mini_endpoint])

    r = test_client.get('/docs/openapi.json')
    assert r.status_code == 200
    assert r.text

    r = test_client.get('/docs', follow_redirects=True)
    assert r.status_code == 200
    assert '<title>Swagger UI</title>' in r.text


# Old test


def test_specification__create_item(fx_app, fx_client):
    def create_item() -> tuple:
        obj = {**request.json, 'uuid': ITEM['uuid']}
        return jsonify(obj), 201

    fx_app.extensions['first'].add_view_func(create_item)

    r_get = fx_client.post(
        '/items', json={'name': ITEM['name'], 'description': ITEM['description']}
    )

    assert r_get.status_code == 201
    assert r_get.json['uuid'] == ITEM['uuid']
    assert r_get.json['name'] == ITEM['name']
    assert r_get.json['description'] == ITEM['description']


def test_specification__items_list(fx_app, fx_client):
    def items_list() -> Response:
        return jsonify([ITEM])

    fx_app.extensions['first'].add_view_func(items_list)

    r_get = fx_client.get('/items')
    assert r_get.status_code == 200
    assert r_get.json[0]
    assert r_get.json[0]['uuid'] == ITEM['uuid']
    assert r_get.json[0]['name'] == ITEM['name']
    assert r_get.json[0]['description'] == ITEM['description']


def test_specification__args(fx_app, fx_client):
    def items_args() -> dict:
        return {
            'page': request.extensions['first']['args']['page'],
            'per_page': request.extensions['first']['args']['per_page'],
            'page_list': request.extensions['first']['args']['page_list'],
        }

    fx_app.extensions['first'].add_view_func(items_args)

    args = {'page': 1000, 'per_page': 10, 'page_list': ['first', 'second']}
    r_get = fx_client.get('/items_args', query_string=args)
    assert r_get.status_code == 200, r_get.json
    assert r_get.json == args


def test_specification__add_route_with_path_parameters(fx_app, fx_client):
    def get_item(uuid: str) -> Response:
        item = {**ITEM, **{'uuid': uuid}}
        return jsonify(item)

    fx_app.extensions['first'].add_view_func(get_item)

    item_uuid = '789d995f-3aa0-4bf8-a37b-2f2f2086d504'
    r_get = fx_client.get(f'/items/{item_uuid}')
    assert r_get.status_code == 200
    assert r_get.json['uuid'] == item_uuid


@pytest.mark.parametrize('path_param', ('BAD_UUID_FORMAT', 1, 1.2, None))
def test_specification__bad_uuid_from_path_params(fx_app, fx_client, path_param):
    def get_item(uuid: str) -> Response:
        item = {**ITEM, **{'uuid': uuid}}
        return jsonify(item)

    fx_app.extensions['first'].add_view_func(get_item)

    with pytest.raises(FirstRequestPathArgsValidation) as e:
        fx_client.get(f'/items/{path_param}')
    assert str(FirstRequestPathArgsValidation) in str(e.type)
    assert "{'uuid': ['Not a valid UUID.']}" in e.value.args[0]


def test_specification__all_type_url_parameters(fx_app, fx_client):
    def get_path_params(path_str: str, path_int: int, path_float: float) -> Response:
        assert isinstance(path_str, str)
        assert isinstance(path_int, int)
        assert isinstance(path_float, float)

        item = {'path_str': path_str, 'path_int': path_int, 'path_float': path_float}
        return jsonify(item)

    fx_app.extensions['first'].add_view_func(get_path_params)

    path_params = {'path_str': 'test_str', 'path_int': 2, 'path_float': 2.3}
    r_get = fx_client.get(
        f'/get_path_params/{path_params["path_str"]}/{path_params["path_int"]}/{path_params["path_float"]}'  # noqa: E501
    )
    assert r_get.status_code == 200
    assert r_get.json['path_str'] == path_params['path_str']
    assert r_get.json['path_int'] == path_params['path_int']
    assert r_get.json['path_float'] == path_params['path_float']


def test_specification__multiple_routes(fx_app, fx_client):
    def first() -> dict:
        return {'message': 'OK'}

    def second() -> dict:
        return {'message': 'OK'}

    fx_app.extensions['first'].add_view_func(first)
    fx_app.extensions['first'].add_view_func(second)

    assert fx_client.get('/first').status_code == 200
    assert fx_client.get('/second').status_code == 200


def test_specification__all_of():
    app = Flask('testing_all_of')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.1.0/all_of.openapi.yaml')
    first = First(full_spec, app)

    def all_of_endpoint() -> dict:
        return {'id': 1, 'name': 'Test_name'}

    first.add_view_func(all_of_endpoint)

    with app.test_client() as test_client:
        assert (
            test_client.post('/all_of_endpoint', json={'id': 1, 'name': 'Test_name'}).status_code
            == 200
        )


def test_specification__one_of():
    app = Flask('testing_one_of')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.1.0/one_of.openapi.yaml')
    first = First(full_spec, app)

    def one_of_endpoint() -> dict:
        return {'name': 'Test_name'}

    first.add_view_func(one_of_endpoint)

    with app.test_client() as test_client:
        assert test_client.get('/one_of_endpoint').status_code == 200


def test_specification__any_of():
    app = Flask('testing_any_of')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.1.0/any_of.openapi.yaml')
    first = First(full_spec, app)

    def any_of_endpoint() -> dict:
        return {'id': 1}

    first.add_view_func(any_of_endpoint)

    with app.test_client() as test_client:
        assert test_client.get('/any_of_endpoint').status_code == 200


def test_specification__not_registered_endpoint():
    app = Flask('not_registered_endpoint')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.1.0/not_registered_endpoint.openapi.yaml')
    First(full_spec, app)

    @app.route('/index')
    def index() -> str:
        return 'OK'

    with app.test_client() as test_client:
        assert test_client.get('/').status_code == 404
        assert test_client.get('/non_exist_endpoint').status_code == 404
        assert test_client.get('/index').status_code == 200


def test_specification__headers():
    app = Flask('endpoint_with_header')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.1.0/headers.openapi.yaml')
    first = First(full_spec, app)

    def endpoint_with_header() -> dict:
        return {'message': request.headers['From-Header']}

    first.add_view_func(endpoint_with_header)

    with app.test_client() as test_client:
        r = test_client.get('/endpoint_with_header', headers={'From-Header': 'test_header'})
        assert r.status_code == 200
        assert r.json['message'] == 'test_header'


def test_specification__registration_function():
    def mini_endpoint() -> dict:
        return {'message': 'test_factory_app'}

    first = First(Path(BASEDIR, 'specs/v3.1.0/mini.openapi.yaml'))

    def create_app():
        app = Flask('factory_app')
        app.debug = 1
        app.testing = 1
        app.config['FIRST_RESPONSE_VALIDATION'] = True
        first.init_app(app)
        first.add_view_func(mini_endpoint)
        return app

    app = create_app()

    with app.test_client() as test_client:
        r = test_client.get('/mini_endpoint')
        assert r.status_code == 200
        assert r.json['message'] == 'test_factory_app'


def test_specification__response_obj():
    def mini_endpoint() -> dict:
        return {'one': {'one_message': 'message'}, 'list': [{'list_message': 'message'}]}

    first = First(Path(BASEDIR, 'specs/v3.1.0/object.openapi.yaml'))

    def create_app():
        app = Flask('object_app')
        app.debug = 1
        app.testing = 1
        app.config['FIRST_RESPONSE_VALIDATION'] = True
        first.init_app(app)
        first.add_view_func(mini_endpoint)
        return app

    app = create_app()

    with app.test_client() as test_client:
        r = test_client.get('/mini_endpoint')
        assert r.status_code == 200
        assert r.json == {'one': {'one_message': 'message'}, 'list': [{'list_message': 'message'}]}


def test_specification__params__format():
    def mini_endpoint(uuid_from_path: str, datetime_from_path: str) -> dict:
        args = request.extensions['first']['args']
        uuid_from_query = args['uuid_from_query']
        datetime_from_query = args['datetime_from_query']

        assert isinstance(uuid_from_query, uuid.UUID)
        assert uuid_from_path == str(uuid_from_query)
        assert datetime_from_path == datetime_from_query.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        return {
            'uuid_from_path': uuid_from_path,
            'uuid_from_query': str(uuid_from_query),
            'datetime_from_query': datetime_from_query.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

    first = First(Path(BASEDIR, 'specs/v3.1.0/parameters.openapi.yaml'))

    def create_app():
        app = Flask('params__format')
        app.debug = 1
        app.testing = 1
        app.config['FIRST_RESPONSE_VALIDATION'] = True
        app.config['FIRST_DATETIME_FORMAT'] = "%Y-%m-%dT%H:%M:%S.%fZ"
        first.init_app(app)
        first.add_view_func(mini_endpoint)
        return app

    app = create_app()

    with app.test_client() as test_client:
        test_uuid = str(uuid.uuid4())
        test_datetime = '2021-12-24T18:32:05.123456Z'
        query_string = {'uuid_from_query': test_uuid, 'datetime_from_query': test_datetime}
        r = test_client.get(
            f'/parameters_endpoint/{test_uuid}/{test_datetime}', query_string=query_string
        )
        assert r.status_code == 200
        assert r.json == {
            'uuid_from_path': test_uuid,
            'uuid_from_query': test_uuid,
            'datetime_from_query': test_datetime,
        }


def test_specification__param_as_list():
    def mini_endpoint() -> dict:
        param_as_list = request.extensions['first']['args']['param_as_list']

        assert isinstance(param_as_list, list)
        assert isinstance(param_as_list[0], uuid.UUID)

        return {'param_as_list': param_as_list}

    first = First(Path(BASEDIR, 'specs/v3.1.0/param_as_list.openapi.yaml'))

    def create_app():
        app = Flask('param_as_list')
        app.debug = 1
        app.testing = 1
        app.config['FIRST_RESPONSE_VALIDATION'] = True
        first.init_app(app)
        first.add_view_func(mini_endpoint)
        return app

    app = create_app()

    with app.test_client() as test_client:
        test_uuid = str(uuid.uuid4())
        r = test_client.get(
            '/parameters_endpoint',
            query_string={'param_as_list': [test_uuid]},
        )
        assert r.status_code == 200
        assert r.json == {'param_as_list': [test_uuid]}


def test_specification__not_defined_name_key():
    app = Flask('testing_not_defined_name_key')
    app.debug = 1
    app.testing = 1
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    full_spec = Path(BASEDIR, 'specs/v3.1.0/not_defined_name_key.openapi.yaml')
    first = First(full_spec, app)

    def one_of_endpoint() -> dict:
        return {'name': 'Test_name'}

    def sub_hashable_obj() -> dict:
        return {'any_field': 'Test_name'}

    first.add_view_func(one_of_endpoint)
    first.add_view_func(sub_hashable_obj)

    with app.test_client() as test_client:
        assert test_client.get('/one_of_endpoint').status_code == 200
        assert test_client.get('/sub_hashable_obj').status_code == 200
