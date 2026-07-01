def create_topic_payload(topic: str):
    return {
        "topic": topic,
        "category": "AI",
        "priority": "HIGH",
    }


def test_update_topic_content_sets_ready_for_review_and_trims_text(client):
    created = client.post("/topics/", json=create_topic_payload("Preview Draft Topic"))
    assert created.status_code == 200

    topic_id = created.json()["id"]
    response = client.put(
        f"/topics/{topic_id}/content",
        json={"generated_post": "  First draft with #Hashtag  "},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "READY_FOR_REVIEW"
    assert body["generated_post"] == "First draft with #Hashtag"


def test_update_topic_content_rejects_empty_draft(client):
    created = client.post("/topics/", json=create_topic_payload("Empty Draft Topic"))
    assert created.status_code == 200

    topic_id = created.json()["id"]
    response = client.put(
        f"/topics/{topic_id}/content",
        json={"generated_post": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Generated content cannot be empty."


def test_approve_after_preview_edit_keeps_content_and_marks_approved(client):
    created = client.post("/topics/", json=create_topic_payload("Approve From Preview Topic"))
    assert created.status_code == 200

    topic_id = created.json()["id"]

    saved = client.put(
        f"/topics/{topic_id}/content",
        json={"generated_post": "Preview-approved content #LinkedIn"},
    )
    assert saved.status_code == 200

    approved = client.post(f"/topics/{topic_id}/approve")
    assert approved.status_code == 200
    approved_body = approved.json()

    assert approved_body["status"] == "APPROVED"
    assert approved_body["generated_post"] == "Preview-approved content #LinkedIn"
