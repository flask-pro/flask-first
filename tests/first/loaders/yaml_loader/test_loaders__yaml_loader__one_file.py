from copy import deepcopy

import pytest

from src.flask_first.first.exceptions import FirstResolverError
from src.flask_first.first.exceptions import FirstYAMLReaderError
from src.flask_first.first.loaders.yaml_loader import load_from_yaml


def test_loaders__yaml__response_ref(fx_spec_minimal, fx_spec_as_file):
    responses_200_ref = {'$ref': '#/components/responses/ItemResponse'}
    responses_schema = {
        'description': 'Response item.',
        'content': {'application/json': {'schema': {'type': 'string'}}},
    }

    fx_spec_minimal['paths']['/endpoint']['get']['responses']['200'] = responses_200_ref
    fx_spec_minimal['components'] = {'responses': {'ItemResponse': responses_schema}}

    spec_file = fx_spec_as_file(fx_spec_minimal)
    spec_obj = load_from_yaml(spec_file)

    assert spec_obj['paths']['/endpoint']['get']['responses']['200'].get('$ref') is None
    assert spec_obj['paths']['/endpoint']['get']['responses']['200'] == responses_schema


def test_loaders_yaml__response_nested_ref(fx_spec_minimal, fx_spec_as_file):
    responses_200_ref = {'$ref': '#/components/responses/ItemResponse'}
    responses_schema = {
        'description': 'Response item.',
        'content': {'application/json': {'schema': {'$ref': '#/components/schemas/FieldSchema'}}},
    }
    field_schema = {'type': 'string'}

    fx_spec_minimal['paths']['/endpoint']['get']['responses']['200'] = responses_200_ref
    fx_spec_minimal['components'] = {'responses': {'ItemResponse': responses_schema}}
    fx_spec_minimal['components'].update({'schemas': {'FieldSchema': field_schema}})

    spec_file = fx_spec_as_file(fx_spec_minimal)
    spec_obj = load_from_yaml(spec_file)

    assert spec_obj['paths']['/endpoint']['get']['responses']['200'].get('$ref') is None
    assert (
        spec_obj['paths']['/endpoint']['get']['responses']['200']['content']['application/json'][
            'schema'
        ].get('$ref')
        is None
    )

    resolved_hierarchy_schema = deepcopy(responses_schema)
    resolved_hierarchy_schema['content']['application/json']['schema'] = field_schema
    assert spec_obj['paths']['/endpoint']['get']['responses']['200'] == resolved_hierarchy_schema


def test_loaders__yaml__parameters_ref(fx_spec_minimal, fx_spec_as_file):
    param_ref = [{'$ref': '#/components/parameters/QueryParam'}]
    param_schema = {
        'name': 'id',
        'in': 'query',
        'schema': {'type': 'array', 'items': {'type': 'string'}},
    }

    fx_spec_minimal['paths']['/endpoint']['parameters'] = param_ref
    fx_spec_minimal['paths']['/endpoint']['get']['parameters'] = param_ref
    fx_spec_minimal['components'] = {'parameters': {'QueryParam': param_schema}}

    spec_file = fx_spec_as_file(fx_spec_minimal)
    spec_obj = load_from_yaml(spec_file)

    assert spec_obj['paths']['/endpoint']['parameters'][0].get('$ref') is None
    assert spec_obj['paths']['/endpoint']['parameters'][0] == param_schema
    assert spec_obj['paths']['/endpoint']['get']['parameters'][0] == param_schema


def test_loader__internal__unknown_ref(fx_spec_minimal, fx_spec_as_file):
    responses_200_ref = {'$ref': '#/components/schemas/NonExistentScheme'}

    fx_spec_minimal['paths']['/endpoint']['get']['responses']['200'] = responses_200_ref

    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)

    with pytest.raises(FirstResolverError) as e:
        load_from_yaml(spec_file)

    assert str(e.value) == 'No such path: "components/schemas/NonExistentScheme"'


@pytest.mark.parametrize('bad_ref', [None, ''])
def test_loader__internal__resolver__bad_ref(fx_spec_minimal, fx_spec_as_file, bad_ref):
    responses_200_ref = {'$ref': bad_ref}
    fx_spec_minimal['paths']['/endpoint']['get']['responses']['200'] = responses_200_ref

    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)

    with pytest.raises(FirstResolverError) as e:
        load_from_yaml(spec_file)

    assert str(e.value) == f'"$ref" with value <{bad_ref}> is not valid in file <{spec_file.name}>'


@pytest.mark.parametrize('bad_ref', [1, '#', '/'])
def test_loader__internal__reader__bad_ref(fx_spec_minimal, fx_spec_as_file, bad_ref):
    responses_200_ref = {'$ref': bad_ref}
    fx_spec_minimal['paths']['/endpoint']['get']['responses']['200'] = responses_200_ref

    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)

    with pytest.raises(FirstYAMLReaderError) as e:
        load_from_yaml(spec_file)

    assert str(e.value) == f'"$ref" with value <{bad_ref}> is not valid.'
