from app.services.generation_service import GenerationService


def test_content_enhance_endpoint_returns_hooks_and_hashtags(client, monkeypatch):
    create_response = client.post(
        '/topics/',
        json={
            'topic': 'Engagement test topic',
            'category': 'AI',
            'priority': 'MEDIUM',
        },
    )
    assert create_response.status_code == 200
    topic_id = create_response.json()['id']

    update_response = client.put(
        f'/topics/{topic_id}/content',
        json={'generated_post': 'Initial draft about AI systems and practical engineering use cases.'},
    )
    assert update_response.status_code == 200

    def fake_enhance(self, topic, engagement_type, extra_keywords, hashtag_count):
        return {
            'success': True,
            'message': 'Engagement enhancement generated successfully.',
            'topic_id': topic.id,
            'engagement_type': engagement_type,
            'optimized_post': 'Optimized post body with stronger opening and CTA.',
            'hooks': [
                'What changed this week in AI that leaders cannot ignore?',
                'One shift in AI tooling is quietly reshaping delivery speed.',
                'If you are building with AI, this pattern matters now.',
            ],
            'hashtags': ['#AI', '#MachineLearning', '#DevOps', '#Automation', '#Innovation', '#TechLeadership'][:hashtag_count],
        }

    monkeypatch.setattr(GenerationService, 'enhance_engagement', fake_enhance)

    response = client.post(
        f'/content/{topic_id}/enhance',
        json={
            'engagement_type': 'how_to_playbook',
            'extra_keywords': ['agents', 'MCP'],
            'hashtag_count': 6,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True
    assert body['topic_id'] == topic_id
    assert body['engagement_type'] == 'how_to_playbook'
    assert len(body['hooks']) == 3
    assert len(body['hashtags']) == 6
    assert 'optimized_post' in body
