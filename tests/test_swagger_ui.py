def test_flask_first__swagger_ui(fx_create_app, fx_get_path_spec_3_2_0):
    def endpoint() -> dict:
        return {'field': 'test_flask_first__swagger_ui'}

    path_to_spec = fx_get_path_spec_3_2_0('mini.openapi.yaml')
    test_client = fx_create_app(path_to_spec, endpoint, '/endpoint')

    r = test_client.get('/endpoint')
    assert r.status_code == 200
    assert r.json['field'] == 'test_flask_first__swagger_ui'

    r = test_client.get('/docs/openapi.json')
    assert r.status_code == 200
    assert r.text

    r = test_client.get('/docs', follow_redirects=True)
    assert r.status_code == 200
    assert '<title>Swagger UI</title>' in r.text
