def test_schedule_settings_persists_when_auto_defaults_disabled(client):
    put_response = client.put(
        "/schedule/settings",
        json={
            "morning_enabled": False,
            "morning_time": "08:00",
            "evening_enabled": False,
            "evening_time": "17:00",
        },
    )

    assert put_response.status_code == 200
    put_body = put_response.json()
    assert put_body["morning_enabled"] is False
    assert put_body["evening_enabled"] is False

    get_response = client.get("/schedule/settings")
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["morning_enabled"] is False
    assert get_body["evening_enabled"] is False
