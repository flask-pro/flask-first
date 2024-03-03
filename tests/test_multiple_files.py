from pathlib import Path

from .conftest import BASEDIR


def test_specification__multiple_files(fx_create_app):
    response = {'message': 'OK'}

    def get_endpoint() -> dict:
        return response

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/multiple_files/valid/openapi.yaml'), [get_endpoint]
    )

    r = test_client.get('/get-endpoint')
    assert r.status_code == 200
    assert r.json == response
