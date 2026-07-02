from pathlib import Path


def test_content_generated_images_endpoint_lists_topic_images(client):
    create_response = client.post(
        '/topics/',
        json={
            'topic': 'Generated image listing topic',
            'category': 'AI',
            'priority': 'MEDIUM',
        },
    )
    assert create_response.status_code == 200
    topic_id = create_response.json()['id']

    generated_dir = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'generated'
    generated_dir.mkdir(parents=True, exist_ok=True)
    image_path = generated_dir / f'topic-{topic_id}-test-preview.png'

    try:
        image_path.write_bytes(b'fake-image-bytes')

        response = client.get(f'/content/{topic_id}/images')
        assert response.status_code == 200
        payload = response.json()
        assert payload['topic_id'] == topic_id
        assert any(f'topic-{topic_id}-test-preview.png' in url for url in payload['image_urls'])
    finally:
        if image_path.exists():
            image_path.unlink()
