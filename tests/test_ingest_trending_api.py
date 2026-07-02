from app.models.topic import Category, Priority
from app.services.trending_service import TrendingService


def test_trending_generate_endpoint_returns_topic_payload(client, monkeypatch):
    def fake_generate(self, engagement_type, category, priority, keyword, max_items, image_count):
        return {
            "success": True,
            "message": "Trending topic created with cumulative summary and generated images.",
            "topic_id": 99,
            "topic": "AI viral trends digest - 2026-07-02 10:00",
            "engagement_type": engagement_type,
            "category": category,
            "priority": priority,
            "generated_post": "Cumulative summary draft",
            "auto_attached_media": True,
            "image_urls": ["http://127.0.0.1:8001/static/generated/a.png"],
            "news_items": [
                {
                    "title": "AI headline",
                    "link": "https://example.com/news/1",
                    "source": "Example",
                    "published": None,
                }
            ],
        }

    monkeypatch.setattr(TrendingService, "generate_trending_topic", fake_generate)

    response = client.post(
        "/ingest/trending",
        json={
            "engagement_type": "trend_radar",
            "category": "AI",
            "keyword": "agents",
            "priority": "HIGH",
            "max_items": 6,
            "image_count": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["topic_id"] == 99
    assert body["engagement_type"] == "trend_radar"
    assert body["category"] == Category.AI
    assert body["priority"] == Priority.HIGH
    assert body["auto_attached_media"] is True
    assert len(body["image_urls"]) == 1
    assert body["news_items"][0]["title"] == "AI headline"
