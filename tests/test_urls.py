from pathlib import Path

import pytest
from flask import request

from .conftest import BASEDIR


@pytest.mark.parametrize(
    'url',
    (
        'http://url-example.com/example',
        'http://url-example.com/example',
        'https://url-example.com/example',
        'ftp://url-example.com/example',
        'ftps://url-example.com/example',
        'http://url-example.com',
        'http://url-example.com:80',
        'http://url-example.com:1234',
        'http://url-example.com/example/example',
        'http://localhost/example/example',
        'http://localhost:1234/example/example',
        'http://127.0.0.1/example/example',
        'http://127.0.0.1:1234/example/example',
        'http://url-example.dev/example/example',
        'http://url-example.dev:1234/example/example',
    ),
)
def test_specification__case_sensitive_url(fx_create_app, url):
    def post_url_format() -> dict:
        return {'url': request.json['url']}

    test_client = fx_create_app(Path(BASEDIR, 'specs/v3.1.0/urls.openapi.yaml'), [post_url_format])

    r = test_client.post('/url_format', json={'url': url})
    assert r.status_code == 200
    assert r.json['url'] == url
