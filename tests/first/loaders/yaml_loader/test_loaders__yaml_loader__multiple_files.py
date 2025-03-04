import pytest

from src.flask_first.first.exceptions import FirstYAMLReaderError
from src.flask_first.first.loaders.yaml_loader import load_from_yaml


def test_loaders__yaml__multiple__response_ref(fx_spec_minimal, fx_spec_as_file):
    endpoint_spec = {'endpoint': fx_spec_minimal['paths']['/endpoint']}
    endpoint_spec['endpoint']['get']['responses']['200']['content']['application/json']['schema'][
        'properties'
    ]['message'] = {'$ref': '#/components/schemas/Message'}
    endpoint_spec['components'] = {'schemas': {'Message': {'type': 'string'}}}
    endpoint_spec_file = fx_spec_as_file(endpoint_spec, validate=False, file_name='endpoint.yaml')

    fx_spec_minimal['paths']['/endpoint'] = {'$ref': f'{endpoint_spec_file.name}#/endpoint'}
    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)
    spec_obj = load_from_yaml(spec_file)

    assert spec_obj['paths']['/endpoint'].get('$ref') is None
    assert spec_obj['paths']['/endpoint']['get']['responses']['200']['content']['application/json'][
        'schema'
    ]['properties']['message'] == {'type': 'string'}


def test_loader__internal__multiple__non_exist_file(fx_spec_minimal, fx_spec_as_file):
    non_exist_file_name = 'non_exist_file.yaml'
    fx_spec_minimal['paths']['/endpoint'] = {'$ref': f'{non_exist_file_name}#/endpoint'}
    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)

    with pytest.raises(FirstYAMLReaderError) as e:
        load_from_yaml(spec_file)

    assert str(e.value) == f'No such file or directory: <{non_exist_file_name}>'


def test_loaders__yaml__multiple__method_as_ref(fx_spec_minimal, fx_spec_as_file, fx_create_app):
    method_spec = {'CORS': {'summary': 'CORS support'}}
    method_spec_file = fx_spec_as_file(method_spec, validate=False, file_name='CORS.openapi.yaml')

    endpoint_spec = {'endpoint': fx_spec_minimal['paths']['/endpoint']}
    endpoint_spec['endpoint']['options'] = {'$ref': f'{method_spec_file.name}#/CORS'}
    endpoint_spec_file = fx_spec_as_file(endpoint_spec, validate=False, file_name='endpoint.yaml')

    fx_spec_minimal['paths']['/endpoint'] = {'$ref': f'{endpoint_spec_file.name}#/endpoint'}
    spec_file = fx_spec_as_file(fx_spec_minimal, validate=False)
    spec_obj = load_from_yaml(spec_file)

    assert spec_obj['paths']['/endpoint'].get('$ref') is None
    assert spec_obj['paths']['/endpoint']['get'] == endpoint_spec['endpoint']['get']
    assert spec_obj['paths']['/endpoint']['options'] == method_spec['CORS']

    def endpoint() -> dict:
        return {'message': 'OK'}

    test_client = fx_create_app(spec_file, [endpoint])
    message = test_client.get('/endpoint')

    assert message.json == {'message': 'OK'}
