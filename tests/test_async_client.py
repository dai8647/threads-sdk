import pytest
import respx
import httpx

from threads_sdk.async_client import AsyncThreadsClient
from threads_sdk.auth import Credentials


@pytest.fixture
def mock_credentials():
    return Credentials(access_token="test_token_123", user_id="12345")


@respx.mock
async def test_async_create_text_post(mock_credentials):
    respx.post("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(200, json={"id": "container_async_001"})
    )
    respx.get("https://graph.threads.net/v1.0/container_async_001").mock(
        return_value=httpx.Response(200, json={"id": "container_async_001", "status": "FINISHED"})
    )
    respx.post("https://graph.threads.net/v1.0/me/threads_publish").mock(
        return_value=httpx.Response(200, json={"id": "post_async_001"})
    )
    async with AsyncThreadsClient(credentials=mock_credentials) as client:
        result = await client.create_text_post("Async hello!")
        assert result.id == "post_async_001"


@respx.mock
async def test_async_get_user_posts(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/12345/threads").mock(
        return_value=httpx.Response(200, json={
            "data": [
                {"id": "p1", "text": "Async Post", "media_type": "TEXT", "username": "testuser"},
            ]
        })
    )
    async with AsyncThreadsClient(credentials=mock_credentials) as client:
        posts = await client.get_user_posts()
        assert len(posts) == 1
        assert posts[0].text == "Async Post"


@respx.mock
async def test_async_get_user_profile(mock_credentials):
    respx.get("https://graph.threads.net/v1.0/12345").mock(
        return_value=httpx.Response(200, json={
            "id": "12345",
            "username": "testuser",
            "name": "Async User",
            "threads_biography": "I async",
        })
    )
    async with AsyncThreadsClient(credentials=mock_credentials) as client:
        profile = await client.get_user_profile()
        assert profile.username == "testuser"
