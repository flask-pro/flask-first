from pathlib import Path

import pytest
from flask import request

from .conftest import BASEDIR


def test_specification__case_sensitive_url(fx_create_app):
    def case_sensitive_url_endpoint() -> dict:
        return {'message': request.url_rule.rule}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.0/url.case_sensitive.openapi.yaml'),
        (case_sensitive_url_endpoint,),
    )

    url = '/CaseSensitiveURL'
    r = test_client.get(url)
    assert r.status_code == 200
    assert r.json['message'] == url


@pytest.mark.parametrize(
    'url', ('/casesensitiveurl', '/casesensitiveurl', '/CASESENSITIVEURL', '/CASE-SENSITIVE_URL')
)
def test_specification__non_case_sensitive_url(fx_create_app, url):
    def case_sensitive_url_endpoint() -> dict:
        return {'message': request.url_rule.rule}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.0/url.case_sensitive.openapi.yaml'),
        (case_sensitive_url_endpoint,),
    )

    r = test_client.get(url)
    assert r.status_code == 404
