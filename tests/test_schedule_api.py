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


def test_manual_queue_scheduling_still_works_when_auto_defaults_disabled(client):
    created = client.post(
        "/topics/",
        json={"topic": "Queue Regression Topic", "category": "AI", "priority": "HIGH"},
    )
    assert created.status_code == 200

    topic_id = created.json()["id"]

    saved = client.put(
        f"/topics/{topic_id}/content",
        json={"generated_post": "Queue-ready content for manual scheduling."},
    )
    assert saved.status_code == 200

    approved = client.post(f"/topics/{topic_id}/approve")
    assert approved.status_code == 200

    settings_response = client.put(
        "/schedule/settings",
        json={
            "morning_enabled": False,
            "morning_time": "08:00",
            "evening_enabled": False,
            "evening_time": "17:00",
        },
    )
    assert settings_response.status_code == 200

    queue_response = client.post(
        "/publish/queue",
        json={
            "topic_id": topic_id,
            "scheduled_for": "2026-07-03T09:00:00Z",
            "max_attempts": 3,
        },
    )

    assert queue_response.status_code == 200
    queue_body = queue_response.json()
    assert queue_body["topic_id"] == topic_id
    assert queue_body["status"] == "PENDING"
