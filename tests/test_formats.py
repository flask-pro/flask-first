from datetime import timezone

from flask import request


def test_request(fx_get_path_spec_3_2_0, fx_create_app):
    def endpoint() -> dict:
        date_time_value = request.extensions['first']['body']['field']

        assert date_time_value.tzinfo == timezone.utc

        return {'field': date_time_value.isoformat()}

    path_to_spec = fx_get_path_spec_3_2_0('date_time.openapi.yaml')
    path = '/endpoint'
    test_client = fx_create_app(path_to_spec, endpoint, path, methods=['POST'])

    json = {'field': '2026-01-01T00:00:00Z'}
    r = test_client.post(path, json=json)
    assert r.status_code == 200
    assert r.json['field'] == '2026-01-01T00:00:00+00:00'
