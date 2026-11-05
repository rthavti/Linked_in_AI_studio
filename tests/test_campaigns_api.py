from io import BytesIO

import pandas as pd


def _build_excel(rows: list[dict]) -> bytes:
    buffer = BytesIO()
    dataframe = pd.DataFrame(rows)
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer.read()


def test_create_learning_campaign_from_excel(client):
    excel_bytes = _build_excel(
        [
            {
                "Day": 1,
                "Series": "LinkedIn AI Studio Content",
                "Phase": "Foundations",
                "Category": "AI Foundations",
                "Topic": "AI Foundations - Topic 1",
                "Subtopic": "Concept 1",
                "Primary Goal": "Save",
                "Hook": "Most engineers misunderstand Concept 1.",
                "Story / Problem": "Teams need a clearer way to explain the architecture.",
                "Teaching Points": "Explain the pattern, tradeoffs, and when to use it.",
                "Enterprise / FDE Angle": "Focus on enterprise implementation and operational concerns.",
                "Suggested Visual": "Architecture / Flow Diagram",
                "Code Demo": "Optional Python demo",
                "Real-world Example": "Enterprise production use case",
                "Opinion": "This pattern is underrated.",
                "CTA": "What challenges have you faced?",
                "Recommended Format": "Text Post",
                "Difficulty": "Beginner",
                "Audience": "Software Engineers, AI Engineers, Tech Leads",
                "Keywords": "architecture, enterprise, ai",
                "Hashtags": "#AI #MLops #LinkedIn",
                "AI Studio Prompt": "Write an enterprise-first post with a practical takeaway.",
                "Status": "Planned",
            },
            {
                "Day": 2,
                "Series": "LinkedIn AI Studio Content",
                "Phase": "Foundations",
                "Category": "AI Foundations",
                "Topic": "AI Foundations - Topic 2",
                "Subtopic": "Concept 2",
                "Primary Goal": "Comment",
                "Hook": "Why does Concept 2 fail in real systems?",
                "Story / Problem": "The gap between theory and deployment is easy to miss.",
                "Teaching Points": "Explain evaluation, safeguards, and rollout patterns.",
                "Enterprise / FDE Angle": "Show the enterprise rollout mindset.",
                "Suggested Visual": "Animated infographic",
                "Code Demo": "Optional Python demo",
                "Real-world Example": "Enterprise production use case",
                "Opinion": "Simple wins over clever.",
                "CTA": "What would you add?",
                "Recommended Format": "Carousel",
                "Difficulty": "Intermediate",
                "Audience": "Software Engineers, AI Engineers, Tech Leads",
                "Keywords": "rollout, evaluation, safeguards",
                "Hashtags": "#AI #EnterpriseAI #LinkedIn",
                "AI Studio Prompt": "Make this practical and discussion-worthy.",
                "Status": "Planned",
            },
            {
                "Day": 3,
                "Series": "LinkedIn AI Studio Content",
                "Phase": "Foundations",
                "Category": "AI Foundations",
                "Topic": "AI Foundations - Topic 3",
                "Subtopic": "Concept 3",
                "Primary Goal": "Share",
                "Difficulty": "Advanced",
                "Status": "Done",
            },
        ]
    )

    response = client.post(
        "/campaigns/upload",
        data={
            "name": "100 Days of Agentic AI",
            "publish_time": "09:00",
            "timezone": "Asia/Kolkata",
            "start_date": "2026-07-03",
            "auto_approve": "true",
            "auto_publish": "true",
            "auto_generate_images": "true",
            "image_count": "2",
            "visual_style": "flow_diagram",
            "max_attempts": "3",
            "min_words": "120",
            "max_words": "320",
        },
        files={"file": ("campaign.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "100 Days of Agentic AI"
    assert payload["status"] == "ACTIVE"
    assert payload["auto_generate_images"] is True
    assert payload["image_count"] == 2
    assert payload["visual_style"] == "flow_diagram"
    assert len(payload["items"]) == 2
    assert payload["items"][0]["day_number"] == 1
    assert payload["items"][1]["day_number"] == 2
    assert payload["items"][0]["topic"] == "AI Foundations - Topic 1 - Concept 1"
    assert "enterprise-first" in (payload["items"][0].get("prompt_brief") or "").lower()
    assert "Preferred visual" in (payload["items"][0].get("visual_hint") or "")
    assert payload["items"][0]["priority"] == "LOW"
    assert payload["items"][1]["priority"] == "MEDIUM"


def test_campaign_upload_requires_topic_column(client):
    excel_bytes = _build_excel(
        [
            {"Name": "Missing topic column", "Category": "AI Foundations", "Status": "Planned"},
        ]
    )

    response = client.post(
        "/campaigns/upload",
        data={
            "name": "Invalid Campaign",
            "publish_time": "09:00",
            "timezone": "Asia/Kolkata",
        },
        files={"file": ("invalid.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 400
    assert "Missing required column" in response.json()["detail"]


def test_campaign_upload_honors_day_column_order(client):
    excel_bytes = _build_excel(
        [
            {"Day": 10, "Topic": "Late topic", "Subtopic": "C", "Category": "AI", "Status": "Planned"},
            {"Day": 1, "Topic": "Early topic", "Subtopic": "A", "Category": "AI", "Status": "Planned"},
            {"Day": 2, "Topic": "Middle topic", "Subtopic": "B", "Category": "AI", "Status": "Planned"},
        ]
    )

    response = client.post(
        "/campaigns/upload",
        data={
            "name": "Day Ordering Campaign",
            "publish_time": "09:00",
            "timezone": "Asia/Kolkata",
        },
        files={"file": ("day-order.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["topic"] for item in payload["items"]] == [
        "Early topic - A",
        "Middle topic - B",
        "Late topic - C",
    ]


def test_delete_planned_campaign(client):
    excel_bytes = _build_excel(
        [
            {"Day": 1, "Topic": "Delete topic 1", "Category": "AI", "Status": "Planned"},
            {"Day": 2, "Topic": "Delete topic 2", "Category": "AI", "Status": "Planned"},
        ]
    )

    create_response = client.post(
        "/campaigns/upload",
        data={
            "name": "Delete Planned Campaign",
            "publish_time": "09:00",
            "timezone": "Asia/Kolkata",
        },
        files={"file": ("delete-campaign.xlsx", excel_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert create_response.status_code == 200
    campaign_id = create_response.json()["id"]

    delete_response = client.delete(f"/campaigns/{campaign_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    list_response = client.get("/campaigns/")
    assert list_response.status_code == 200
    campaign_ids = [row["id"] for row in list_response.json()]
    assert campaign_id not in campaign_ids
