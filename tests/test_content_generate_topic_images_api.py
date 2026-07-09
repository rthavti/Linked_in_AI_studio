from app.services.generation_service import GenerationService


def test_generate_images_for_topic_endpoint(client, monkeypatch):
    create_response = client.post(
        '/topics/',
        json={
            'topic': 'AI governance matrix for enterprise adoption',
            'category': 'AI',
            'priority': 'MEDIUM',
        },
    )
    assert create_response.status_code == 200
    topic_id = create_response.json()['id']

    client.put(
        f'/topics/{topic_id}/content',
        json={'generated_post': 'Use a decision matrix to choose where AI should and should not be used.'},
    )

    monkeypatch.setattr(GenerationService, 'generate_images_for_topic', lambda *args, **kwargs: ['http://test/image.png'])

    response = client.post(
        f'/content/{topic_id}/generate-images',
        json={
            'image_count': 1,
            'visual_template': 'matrix_2x2',
            'image_size': '1536x1024',
            'image_style_hint': 'clean editorial infographic',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['topic_id'] == topic_id
    assert isinstance(payload['image_urls'], list)
