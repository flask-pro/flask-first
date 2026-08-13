from pathlib import Path

from flask import request
from flask import send_file

from tests.conftest import BASEDIR


def test_files(fx_get_path_spec_3_2_0, fx_create_app):
    def upload_file() -> tuple:
        assert request.files.get('file')
        return '', 204

    path_to_spec = fx_get_path_spec_3_2_0('request_body/files.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, upload_file, path, methods=['POST'])

    headers = {'Content-Type': 'multipart/form-data'}
    data = {'file': open(Path(BASEDIR, 'content/img.png'), mode='rb')}
    uploaded_file = test_client.post(path, headers=headers, data=data)
    assert uploaded_file.status_code == 204

    def download_file():
        response = send_file(Path(BASEDIR, 'content/img.png'), download_name='img.png')
        response.direct_passthrough = False
        return response

    test_client = fx_create_app(path_to_spec, download_file, path, methods=['GET'])

    downloaded_file = test_client.get(path)
    assert downloaded_file.status_code == 200
    assert downloaded_file.data
