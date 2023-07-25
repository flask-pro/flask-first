from pathlib import Path

import pytest
from flask import request
from flask_first.first.exceptions import FirstRequestArgsValidation
from flask_first.first.exceptions import FirstRequestPathArgsValidation

from .conftest import BASEDIR


def test_specification__non_exist_args(fx_create_app):
    def mini_endpoint() -> dict:
        args = request.first_args
        assert args.get('non_exist_arg') is None

        return {'non_exist_arg': None}

    test_client = fx_create_app(Path(BASEDIR, 'specs/v3.0/args.openapi.yaml'), (mini_endpoint,))

    with pytest.raises(FirstRequestArgsValidation):
        test_client.get(
            '/parameters_endpoint',
            query_string={'non_exist_arg': 'NON_EXIST_ARGS'},
        )


def test_specification__required_args(fx_create_app):
    def mini_endpoint(required_path) -> dict:
        required_arg = request.first_args['required_arg']

        return {'required_path': required_path, 'required_arg': required_arg}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.0/args.required.openapi.yaml'), (mini_endpoint,)
    )

    with pytest.raises(FirstRequestPathArgsValidation):
        test_client.get(
            '/parameters_endpoint/not_exist_params', query_string={'required_arg': 'EXIST_ARGS'}
        )

    with pytest.raises(FirstRequestArgsValidation):
        test_client.get('/parameters_endpoint/params_from_enum')

    with pytest.raises(FirstRequestArgsValidation) as e:
        test_client.get(
            '/parameters_endpoint/params_from_enum', query_string={'non_required_arg': 'EXIST_ARGS'}
        )
    assert (
        e.value.args[0] == "{'required_arg': ['Missing data for required field.'], "
        "'non_required_arg': ['Unknown field.']}"
    )

    r = test_client.get(
        '/parameters_endpoint/params_from_enum', query_string={'required_arg': 'EXIST_ARGS'}
    )
    assert r.status_code == 200
    assert r.json['required_arg'] == 'EXIST_ARGS'


def test_specification__endpoint_without_args(fx_create_app):
    def without_args_endpoint() -> dict:
        return {'message': 'No args.'}

    test_client = fx_create_app(
        Path(BASEDIR, 'specs/v3.0/args.required.openapi.yaml'), (without_args_endpoint,)
    )

    with pytest.raises(FirstRequestArgsValidation):
        test_client.get('/without_args_endpoint', query_string={'required_arg': 'EXIST_ARGS'})

    r = test_client.get('/without_args_endpoint')
    assert r.status_code == 200
    assert r.json['message'] == 'No args.'
