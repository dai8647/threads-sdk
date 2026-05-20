"""Pydantic models for Threads API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class UserProfile(BaseModel):
    """Threads user profile."""

    id: str
    username: str
    name: str = ""
    threads_profile_picture_url: str = ""
    threads_biography: str = ""

    @property
    def biography(self) -> str:
        return self.threads_biography


class ThreadsPost(BaseModel):
    """A Threads post (thread)."""

    id: str
    text: str = ""
    timestamp: str = ""
    permalink: str = ""
    media_type: str = "TEXT"
    media_url: Optional[str] = None
    username: str = ""
    shortcode: Optional[str] = None
    is_quote_post: bool = False
    quoted_post_id: Optional[str] = None
    root_post_id: Optional[str] = None
    reply_to_id: Optional[str] = None


class PostReply(BaseModel):
    """A reply to a Threads post."""

    id: str
    text: str = ""
    timestamp: str = ""
    username: str = ""
    media_type: str = "TEXT"
    media_url: Optional[str] = None


class InsightMetric(BaseModel):
    """A single insight metric."""

    name: str
    values: list[dict[str, int]] = Field(default_factory=list)

    @property
    def value(self) -> int:
        return self.values[0]["value"] if self.values else 0


class PostInsights(BaseModel):
    """Insights for a Threads post."""

    data: list[InsightMetric] = Field(default_factory=list)

    @property
    def views(self) -> int:
        return self._get_metric("views")

    @property
    def likes(self) -> int:
        return self._get_metric("likes")

    @property
    def replies(self) -> int:
        return self._get_metric("replies")

    @property
    def reposts(self) -> int:
        return self._get_metric("reposts")

    @property
    def quotes(self) -> int:
        return self._get_metric("quotes")

    def _get_metric(self, name: str) -> int:
        for metric in self.data:
            if metric.name == name:
                return metric.value
        return 0


class ContainerStatus(BaseModel):
    """Status of a content container."""

    id: str
    status: str
    error: Optional[dict[str, str]] = None

    @property
    def is_ready(self) -> bool:
        return self.status == "FINISHED"


class TokenResponse(BaseModel):
    """OAuth token response."""

    access_token: str
    user_id: str = ""
    expires_in: Optional[int] = None


class LongLivedTokenResponse(BaseModel):
    """Long-lived token response after refresh."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 0
