"""Asynchronous Threads API client."""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx

from threads_sdk.auth import Credentials
from threads_sdk.exceptions import (
    ThreadsError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)
from threads_sdk.models import (
    ContainerStatus,
    PostInsights,
    PostReply,
    ThreadsPost,
    UserProfile,
)

GRAPH_API_BASE = "https://graph.threads.net"


class AsyncThreadsClient:
    """Asynchronous client for Meta's Threads API."""

    def __init__(
        self,
        credentials: Credentials,
        base_url: str = GRAPH_API_BASE,
    ) -> None:
        self.credentials = credentials
        self._client = httpx.AsyncClient(
            base_url=base_url,
            params={"access_token": credentials.access_token},
            timeout=30.0,
        )

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an API request and handle errors."""
        response = await self._client.request(method, path, **kwargs)
        if response.status_code == 400:
            error = response.json().get("error", {})
            raise ValidationError(error.get("message", "Validation error"))
        if response.status_code == 401:
            error = response.json().get("error", {})
            raise AuthenticationError(error.get("message", "Authentication failed"))
        if response.status_code == 404:
            error = response.json().get("error", {})
            raise NotFoundError(error.get("message", "Not found"))
        if response.status_code == 429:
            error = response.json().get("error", {})
            raise RateLimitError(error.get("message", "Rate limit exceeded"))
        if response.status_code >= 400:
            error = response.json().get("error", {})
            raise ThreadsError(error.get("message", f"API error {response.status_code}"))
        return response

    async def _wait_for_container(self, container_id: str, timeout: int = 60) -> ContainerStatus:
        """Poll until container is ready or timeout."""
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            response = await self._request("GET", f"/{container_id}")
            status = ContainerStatus(**response.json())
            if status.is_ready:
                return status
            if status.error:
                raise ThreadsError(f"Container error: {status.error}")
            await asyncio.sleep(1)
        raise ThreadsError(f"Container {container_id} not ready after {timeout}s")

    async def _create_and_publish(
        self,
        user_id: str,
        media_type: str,
        text: str = "",
        media_url: Optional[str] = None,
        reply_to_id: Optional[str] = None,
    ) -> ThreadsPost:
        """Create a container, wait for processing, and publish."""
        payload: dict = {"media_type": media_type}
        if text:
            payload["text"] = text
        if media_url:
            payload["media_url"] = media_url
        if reply_to_id:
            payload["reply_to_id"] = reply_to_id

        response = await self._request("POST", f"/{user_id}/threads", data=payload)
        container_id = response.json()["id"]

        await self._wait_for_container(container_id)

        response = await self._request("POST", f"/{container_id}/publish")
        return ThreadsPost(id=response.json()["id"], text=text, media_type=media_type)

    async def create_text_post(self, text: str) -> ThreadsPost:
        """Publish a text-only post."""
        return await self._create_and_publish(
            user_id=self.credentials.user_id,
            media_type="TEXT",
            text=text,
        )

    async def create_image_post(self, image_url: str, text: str = "") -> ThreadsPost:
        """Publish a post with an image."""
        return await self._create_and_publish(
            user_id=self.credentials.user_id,
            media_type="IMAGE",
            text=text,
            media_url=image_url,
        )

    async def create_video_post(self, video_url: str, text: str = "") -> ThreadsPost:
        """Publish a post with a video."""
        return await self._create_and_publish(
            user_id=self.credentials.user_id,
            media_type="VIDEO",
            text=text,
            media_url=video_url,
        )

    async def reply_to_post(self, post_id: str, text: str) -> ThreadsPost:
        """Reply to an existing post."""
        return await self._create_and_publish(
            user_id=self.credentials.user_id,
            media_type="TEXT",
            text=text,
            reply_to_id=post_id,
        )

    async def get_user_posts(self, limit: int = 25) -> list[ThreadsPost]:
        """Get the authenticated user's posts."""
        response = await self._request(
            "GET",
            f"/{self.credentials.user_id}/threads",
            params={"fields": "id,text,timestamp,permalink,media_type,media_url,username", "limit": limit},
        )
        data = response.json().get("data", [])
        return [ThreadsPost(**post) for post in data]

    async def get_post_replies(self, post_id: str) -> list[PostReply]:
        """Get replies to a post."""
        response = await self._request("GET", f"/{post_id}/replies")
        data = response.json().get("data", [])
        return [PostReply(**reply) for reply in data]

    async def get_post_insights(self, post_id: str) -> PostInsights:
        """Get insights/metrics for a post."""
        response = await self._request(
            "GET",
            f"/{post_id}/insights",
            params={"metric": "views,likes,replies,reposts,quotes"},
        )
        return PostInsights(**response.json())

    async def get_user_profile(self, user_id: Optional[str] = None) -> UserProfile:
        """Get a user's profile."""
        uid = user_id or self.credentials.user_id
        response = await self._request("GET", f"/{uid}")
        return UserProfile(**response.json())

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncThreadsClient:
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
