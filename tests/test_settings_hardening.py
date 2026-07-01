def test_oauth_health_endpoint_returns_readiness_flags(client):
    response = client.get('/publish/oauth/health')

    assert response.status_code == 200
    body = response.json()

    assert 'oauth_configured' in body
    assert 'client_id_configured' in body
    assert 'retry_delay_seconds' in body
    assert 'connected' in body


def test_schedule_settings_allows_auto_defaults_disabled(client):
    response = client.put(
        '/schedule/settings',
        json={
            'morning_enabled': False,
            'morning_time': '08:00',
            'evening_enabled': False,
            'evening_time': '17:00',
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body['morning_enabled'] is False
    assert body['evening_enabled'] is False


def test_schedule_settings_rejects_duplicate_enabled_times(client):
    response = client.put(
        '/schedule/settings',
        json={
            'morning_enabled': True,
            'morning_time': '08:00',
            'evening_enabled': True,
            'evening_time': '08:00',
        },
    )

    assert response.status_code == 422
