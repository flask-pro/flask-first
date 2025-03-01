import pytest

from src.flask_first.first.exceptions import FirstYAMLReaderError
from src.flask_first.first.loaders.yaml_loader import load_from_yaml


def test_loaders__yaml__multiple__response_ref(fx_spec_minimal, fx_spec_as_file):
    endpoint_spec = {'endpoint': fx_spec_minimal['paths']['/endpoint']}
    endpoint_spec_file = fx_spec_as_file(endpoint_spec, validate=False, file_name='endpoint.yaml')

    fx_spec_minimal['paths']['/endpoint'] = {'$ref': f'{endpoint_spec_file.name}#/endpoint'}
    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)
    spec_obj = load_from_yaml(spec_file)

    assert spec_obj['paths']['/endpoint'].get('$ref') is None
    assert spec_obj['paths']['/endpoint'] == endpoint_spec['endpoint']


def test_loader__internal__multiple__non_exist_file(fx_spec_minimal, fx_spec_as_file):
    non_exist_file_name = 'non_exist_file.yaml'
    fx_spec_minimal['paths']['/endpoint'] = {'$ref': f'{non_exist_file_name}#/endpoint'}
    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)

    with pytest.raises(FirstYAMLReaderError) as e:
        load_from_yaml(spec_file)

    assert str(e.value) == f'No such file or directory: <{non_exist_file_name}>'
