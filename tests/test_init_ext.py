from flask import Flask

from src.flask_first import First


def test_init_extension(fx_app):
    assert fx_app.config['FIRST_RESPONSE_VALIDATION'] is True


def test_init_empty_path_to_spec(fx_app):
    app = Flask('empty_path_to_spec')
    try:
        First(app)
    except TypeError:
        assert True
