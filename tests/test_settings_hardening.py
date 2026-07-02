from app.config.settings import settings


def test_oauth_health_endpoint_returns_readiness_flags(client):
    response = client.get('/publish/oauth/health')

    assert response.status_code == 200
    body = response.json()

    assert 'oauth_configured' in body
    assert 'client_id_configured' in body
    assert 'retry_delay_seconds' in body
    assert 'connected' in body


def test_oauth_connect_reports_missing_configuration(client, monkeypatch):
    monkeypatch.setattr(settings, 'LINKEDIN_CLIENT_ID', '')
    monkeypatch.setattr(settings, 'LINKEDIN_CLIENT_SECRET', '')
    monkeypatch.setattr(settings, 'LINKEDIN_REDIRECT_URI', '')

    response = client.get('/publish/connect')

    assert response.status_code == 400
    body = response.json()
    assert 'LinkedIn OAuth settings are not configured.' in body['detail']
    assert 'LINKEDIN_CLIENT_ID' in body['detail']
    assert 'LINKEDIN_CLIENT_SECRET' in body['detail']
    assert 'LINKEDIN_REDIRECT_URI' in body['detail']


def test_oauth_callback_surfaces_provider_error(client):
    response = client.get(
        '/publish/callback',
        params={
            'error': 'unauthorized_scope_error',
            'error_description': 'Scope+%26quot%3Br_liteprofile%26quot%3B+is+not+authorized+for+your+application',
            'state': 'fake-state',
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert 'LinkedIn OAuth failed: unauthorized_scope_error' in body['detail']
    assert 'r_liteprofile' in body['detail']
    assert 'Verify LINKEDIN_SCOPES matches permissions enabled for your LinkedIn app' in body['detail']


def test_oauth_callback_missing_code_or_state_returns_400(client):
    response = client.get('/publish/callback', params={'state': 'fake-state'})

    assert response.status_code == 400
    body = response.json()
    assert 'missing required query parameters' in body['detail']


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
