from pathlib import Path

import pytest
from flask import request

from .conftest import BASEDIR


def test_specification__case_sensitive_url(fx_create_app):
    def non_case_sensitive_url_endpoint() -> dict:
        return {'message': request.url_rule.rule}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.0/url.non_case_sensitive.openapi.yaml'),
        (non_case_sensitive_url_endpoint,),
    )

    url = '/NonCaseSensitiveURL'
    r = test_client.get(url)
    assert r.status_code == 200
    assert r.json['message'] == url


@pytest.mark.parametrize(
    'url', ('/noncasesensitiveurl', '/Noncasesensitiveurl', '/NONCASESENSITIVEURL')
)
def test_specification__non_case_sensitive_url(fx_create_app, url):
    def non_case_sensitive_url_endpoint() -> dict:
        return {'message': request.url}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.0/url.non_case_sensitive.openapi.yaml'),
        (non_case_sensitive_url_endpoint,),
    )

    r = test_client.get(url)
    assert r.status_code == 404
