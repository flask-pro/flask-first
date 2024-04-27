from flask_first import request


def test_tools__json(fx_make_spec_file, fx_create_app):
    spec_path = fx_make_spec_file()

    def post_endpoint() -> tuple[dict, int]:
        json = request.extensions['first']['json']
        return json, 201

    test_client = fx_create_app(spec_path, [post_endpoint])

    r = test_client.post('/endpoint', json={'message': 'OK'})
    assert r.status_code == 201
    assert r.json == {'message': 'OK'}


def test_tools__args(fx_make_spec_file, fx_create_app):
    parameters = [{'name': 'message', 'in': 'query', 'schema': {'type': 'string'}}]
    spec_path = fx_make_spec_file(parameters=parameters)

    def get_endpoint() -> tuple[dict, int]:
        args = request.extensions['first']['args']
        return args

    test_client = fx_create_app(spec_path, [get_endpoint])

    r = test_client.get('/endpoint', query_string={'message': 'OK'})
    assert r.status_code == 200
    assert r.json == {'message': 'OK'}


def test_tools__view_args(fx_make_spec_file, fx_create_app):
    url = '/endpoint/{message}'
    parameters = [{'name': 'message', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}]
    spec_path = fx_make_spec_file(url=url, parameters=parameters)

    def get_endpoint(message) -> tuple[dict, int]:
        view_args = request.extensions['first']['view_args']
        return view_args

    test_client = fx_create_app(spec_path, [get_endpoint])

    r = test_client.get('/endpoint/OK')
    assert r.status_code == 200
    assert r.json == {'message': 'OK'}
