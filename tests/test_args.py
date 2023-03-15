from pathlib import Path

import pytest
from flask import Flask
from flask import request
from flask_first import First
from flask_first.exceptions import FirstRequestArgsValidation

from .conftest import BASEDIR


def test_specification__non_exist_args():
    def mini_endpoint() -> dict:
        args = request.first_args
        assert args.get('non_exist_arg') is None

        return {'non_exist_arg': None}

    first = First(Path(BASEDIR, 'specs/v3.0/args.openapi.yaml'))

    def create_app():
        app = Flask('non_exist_args')
        app.debug = 1
        app.testing = 1
        app.config['FIRST_RESPONSE_VALIDATION'] = True
        first.init_app(app)
        first.add_view_func(mini_endpoint)
        return app

    app = create_app()

    with pytest.raises(FirstRequestArgsValidation) as e:
        app.test_client().get(
            '/parameters_endpoint',
            query_string={'non_exist_arg': 'NON_EXIST_ARGS'},
        )
    assert str(FirstRequestArgsValidation) in str(e.type)
