import pytest
import respx
import httpx

from threads_sdk.client import ThreadsClient
from threads_sdk.auth import Credentials
from threads_sdk.exceptions import ThreadsError, NotFoundError, RateLimitError


@respx.mock
def test_create_text_post(mock_credentials):
    respx.post("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(200, json={"id": "container_001"})
    )
    respx.get("https://graph.threads.net/v1.0/container_001").mock(
        return_value=httpx.Response(200, json={"id": "container_001", "status": "FINISHED"})
    )
    respx.post("https://graph.threads.net/v1.0/me/threads_publish").mock(
        return_value=httpx.Response(200, json={"id": "post_001"})
    )
    client = ThreadsClient(credentials=mock_credentials)
    result = client.create_text_post("Hello World!")
    assert result.id == "post_001"


@respx.mock
def test_create_image_post(mock_credentials):
    respx.post("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(200, json={"id": "container_002"})
    )
    respx.get("https://graph.threads.net/v1.0/container_002").mock(
        return_value=httpx.Response(200, json={"id": "container_002", "status": "FINISHED"})
    )
    respx.post("https://graph.threads.net/v1.0/me/threads_publish").mock(
        return_value=httpx.Response(200, json={"id": "post_002"})
    )
    client = ThreadsClient(credentials=mock_credentials)
    result = client.create_image_post("https://example.com/photo.jpg", text="Check this out!")
    assert result.id == "post_002"


@respx.mock
def test_get_user_posts(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(200, json={
            "data": [
                {"id": "p1", "text": "Post 1", "media_type": "TEXT", "username": "testuser"},
                {"id": "p2", "text": "Post 2", "media_type": "TEXT", "username": "testuser"},
            ]
        })
    )
    client = ThreadsClient(credentials=mock_credentials)
    posts = client.get_user_posts(limit=10)
    assert len(posts) == 2
    assert posts[0].id == "p1"
    assert posts[1].text == "Post 2"


@respx.mock
def test_get_post_replies(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/post_123/replies").mock(
        return_value=httpx.Response(200, json={
            "data": [
                {"id": "reply_1", "text": "Nice!", "username": "someone"},
            ]
        })
    )
    client = ThreadsClient(credentials=mock_credentials)
    replies = client.get_post_replies("post_123")
    assert len(replies) == 1
    assert replies[0].text == "Nice!"


@respx.mock
def test_get_post_insights(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/post_123/insights").mock(
        return_value=httpx.Response(200, json={
            "data": [
                {"name": "views", "values": [{"value": 1000}]},
                {"name": "likes", "values": [{"value": 50}]},
            ]
        })
    )
    client = ThreadsClient(credentials=mock_credentials)
    insights = client.get_post_insights("post_123")
    assert insights.views == 1000
    assert insights.likes == 50


@respx.mock
def test_get_user_profile(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/12345").mock(
        return_value=httpx.Response(200, json={
            "id": "12345",
            "username": "testuser",
            "name": "Test User",
            "threads_biography": "I code",
        })
    )
    client = ThreadsClient(credentials=mock_credentials)
    profile = client.get_user_profile()
    assert profile.username == "testuser"
    assert profile.name == "Test User"


@respx.mock
def test_reply_to_post(mock_credentials):
    respx.post("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(200, json={"id": "container_reply"})
    )
    respx.get("https://graph.threads.net/v1.0/container_reply").mock(
        return_value=httpx.Response(200, json={"id": "container_reply", "status": "FINISHED"})
    )
    respx.post("https://graph.threads.net/v1.0/me/threads_publish").mock(
        return_value=httpx.Response(200, json={"id": "reply_post_001"})
    )
    client = ThreadsClient(credentials=mock_credentials)
    result = client.reply_to_post("original_post_id", "Great post!")
    assert result.id == "reply_post_001"


@respx.mock
def test_client_handles_rate_limit(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(429, json={
            "error": {"message": "Rate limit exceeded", "type": "OAuthException"}
        })
    )
    client = ThreadsClient(credentials=mock_credentials)
    with pytest.raises(RateLimitError):
        client.get_user_posts()


@respx.mock
def test_client_handles_not_found(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/nonexistent").mock(
        return_value=httpx.Response(404, json={
            "error": {"message": "Not found", "type": "OAuthException"}
        })
    )
    client = ThreadsClient(credentials=mock_credentials)
    with pytest.raises(NotFoundError):
        client._request("GET", "/nonexistent")
