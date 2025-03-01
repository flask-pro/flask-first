from pathlib import Path

import pytest
import yaml
from openapi_spec_validator import validate as osv_validate
from openapi_spec_validator.readers import read_from_filename


@pytest.fixture
def fx_spec_minimal():
    payload = {
        'openapi': '3.1.1',
        'info': {'title': 'API for testing Flask-First', 'version': '1.0.0'},
        'paths': {
            '/endpoint': {
                'get': {
                    'operationId': 'endpoint',
                    'responses': {
                        '200': {
                            'description': 'OK',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {'message': {'type': 'string'}},
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }
    return payload


@pytest.fixture
def fx_spec_as_file(tmp_path):
    def create(spec: dict, validate: bool = True, file_name: str = 'openapi.yaml') -> Path:
        spec_path = Path(tmp_path, file_name)
        with open(spec_path, 'w+') as f:
            yaml.dump(spec, f)

        spec_as_dict, _ = read_from_filename(str(spec_path))
        if validate:
            osv_validate(spec_as_dict)

        return spec_path

    return create
