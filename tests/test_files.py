from flask import Flask
from flask import request
from flask import send_file
from flask_first import First


def test_files(fx_app, fx_client):
    app = Flask('check_v30_specs')
    app.config['FIRST_RESPONSE_VALIDATION'] = True
    first = First('specs/v3.0/files.openapi.yaml', app=app, swagger_ui_path='/docs')

    def upload_file() -> tuple:
        assert request.files.get('file')
        return '', 204

    def download_file():
        response = send_file('content/img.png', download_name='img.png')
        response.direct_passthrough = False
        return response

    first.add_view_func(upload_file)
    first.add_view_func(download_file)

    uploaded_file = app.test_client().post(
        '/files',
        headers={'Content-Type': 'multipart/form-data'},
        data={'file': open('content/img.png', mode='rb')},
    )

    assert uploaded_file.status_code == 204

    downloaded_file = app.test_client().get('/files')
    assert downloaded_file.status_code == 200
    assert downloaded_file.data
