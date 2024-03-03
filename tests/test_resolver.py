from pathlib import Path

import pytest

from .conftest import BASEDIR
from src.flask_first.first.exceptions import FirstOpenAPIResolverError
from src.flask_first.first.specification import Resolver

MULTIPLE_FILES_NOT_VALID_PATH = Path(BASEDIR, 'specs/multiple_files/not_valid')


def test_resolver__one_file():
    spec_file = Path(BASEDIR, 'specs/v3.1.0/ref.openapi.yaml')
    resolve = Resolver(spec_file)
    resolved_spec = resolve.resolve()

    mini_endpoint = resolved_spec['paths']['/mini_endpoint/{uuid}']
    components = resolved_spec['components']

    assert mini_endpoint['parameters'][0].get('$ref') is None
    assert mini_endpoint['parameters'][0] == components['parameters']['uuid']

    assert mini_endpoint['post']['parameters'][0].get('$ref') is None
    assert mini_endpoint['post']['parameters'][0] == components['parameters']['page']

    assert mini_endpoint['post']['requestBody'].get('$ref') is None
    assert mini_endpoint['post']['requestBody'] == components['requestBodies']['ItemRequest']

    assert mini_endpoint['post']['responses']['200'].get('$ref') is None
    assert mini_endpoint['post']['responses']['200'] == components['responses']['ItemResponse']


def test_resolver__multiple_files():
    spec_file = Path(BASEDIR, 'specs/multiple_files/valid/openapi.yaml')
    resolve = Resolver(spec_file)
    resolved_spec = resolve.resolve()

    get_endpoint = resolved_spec['paths']['/get-endpoint']

    assert get_endpoint.get('$ref') is None
    assert get_endpoint['get']


@pytest.mark.parametrize(
    'spec',
    MULTIPLE_FILES_NOT_VALID_PATH.iterdir(),
    ids=[file.name for file in MULTIPLE_FILES_NOT_VALID_PATH.iterdir()],
)
def test_resolver__not_valid(spec):
    resolve = Resolver(spec)

    with pytest.raises(FirstOpenAPIResolverError):
        resolve.resolve()
