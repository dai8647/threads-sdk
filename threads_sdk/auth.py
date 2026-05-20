"""OAuth 2.0 authentication and token management for Threads API."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import httpx

from threads_sdk.exceptions import AuthenticationError
from threads_sdk.models import LongLivedTokenResponse

GRAPH_API_BASE = "https://graph.threads.net"


@dataclass
class Credentials:
    """Stores API credentials."""

    access_token: str
    user_id: str = ""
    expires_at: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        import time
        return time.time() >= self.expires_at

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> Credentials:
        return cls(**json.loads(data))

    def save(self, path: Path | str) -> None:
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> Credentials:
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


class Auth:
    """Handles OAuth 2.0 flow for Threads API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str = "",
        redirect_uri: str = "",
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._client = httpx.Client(base_url=GRAPH_API_BASE)

    def get_authorization_url(self, state: str = "") -> str:
        """Generate the OAuth authorization URL for user consent."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "threads_basic,threads_content_publish,threads_manage_replies,threads_manage_insights,threads_read_replies",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        return f"https://threads.net/oauth/authorize?{urlencode(params)}"

    def exchange_code(self, code: str) -> Credentials:
        """Exchange authorization code for short-lived access token."""
        response = self._client.post(
            "/oauth/access_token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        if response.status_code != 200:
            error = response.json().get("error", {})
            raise AuthenticationError(error.get("message", "Token exchange failed"))
        data = response.json()
        return Credentials(
            access_token=data["access_token"],
            user_id=str(data.get("user_id", "")),
        )

    def get_long_lived_token(self, short_token: str) -> LongLivedTokenResponse:
        """Exchange short-lived token for long-lived token (60 days)."""
        response = self._client.get(
            "/oauth/access_token",
            params={
                "grant_type": "th_exchange_token",
                "client_secret": self.client_secret,
                "access_token": short_token,
            },
        )
        if response.status_code != 200:
            error = response.json().get("error", {})
            raise AuthenticationError(error.get("message", "Token exchange failed"))
        return LongLivedTokenResponse(**response.json())

    def refresh_token(self, long_token: str) -> LongLivedTokenResponse:
        """Refresh a long-lived token (extends by 60 days)."""
        response = self._client.get(
            "/refresh_access_token",
            params={
                "grant_type": "th_refresh_token",
                "access_token": long_token,
            },
        )
        if response.status_code != 200:
            error = response.json().get("error", {})
            raise AuthenticationError(error.get("message", "Token refresh failed"))
        return LongLivedTokenResponse(**response.json())
