from datetime import datetime
from threads_sdk.models import (
    UserProfile,
    ThreadsPost,
    PostReply,
    PostInsights,
    ContainerStatus,
    TokenResponse,
)


def test_user_profile_from_api():
    data = {
        "id": "12345",
        "username": "testuser",
        "name": "Test User",
        "threads_profile_picture_url": "https://example.com/pic.jpg",
        "threads_biography": "Hello world",
    }
    profile = UserProfile(**data)
    assert profile.id == "12345"
    assert profile.username == "testuser"
    assert profile.name == "Test User"
    assert profile.biography == "Hello world"


def test_threads_post_from_api():
    data = {
        "id": "98765",
        "text": "Hello from threads-sdk!",
        "timestamp": "2026-05-20T12:00:00+0000",
        "permalink": "https://threads.net/testuser/post/98765",
        "media_type": "TEXT",
        "username": "testuser",
    }
    post = ThreadsPost(**data)
    assert post.id == "98765"
    assert post.text == "Hello from threads-sdk!"
    assert post.media_type == "TEXT"
    assert post.permalink == "https://threads.net/testuser/post/98765"


def test_threads_post_with_media():
    data = {
        "id": "98766",
        "text": "Photo post",
        "timestamp": "2026-05-20T12:00:00+0000",
        "permalink": "https://threads.net/testuser/post/98766",
        "media_type": "IMAGE",
        "media_url": "https://example.com/photo.jpg",
        "username": "testuser",
    }
    post = ThreadsPost(**data)
    assert post.media_type == "IMAGE"
    assert post.media_url == "https://example.com/photo.jpg"


def test_post_reply():
    data = {
        "id": "11111",
        "text": "Nice post!",
        "timestamp": "2026-05-20T13:00:00+0000",
        "username": "replier",
    }
    reply = PostReply(**data)
    assert reply.id == "11111"
    assert reply.text == "Nice post!"


def test_post_insights():
    data = {
        "data": [
            {"name": "views", "values": [{"value": 1500}]},
            {"name": "likes", "values": [{"value": 42}]},
            {"name": "replies", "values": [{"value": 7}]},
        ]
    }
    insights = PostInsights(**data)
    assert insights.views == 1500
    assert insights.likes == 42
    assert insights.replies == 7


def test_container_status():
    data = {"id": "container_123", "status": "FINISHED"}
    container = ContainerStatus(**data)
    assert container.id == "container_123"
    assert container.status == "FINISHED"
    assert container.is_ready is True


def test_container_status_not_ready():
    data = {"id": "container_123", "status": "IN_PROGRESS"}
    container = ContainerStatus(**data)
    assert container.is_ready is False


def test_token_response():
    data = {
        "access_token": "short_lived_token",
        "user_id": "12345",
    }
    token = TokenResponse(**data)
    assert token.access_token == "short_lived_token"
    assert token.user_id == "12345"
