import json
import pytest
from pathlib import Path
from unittest.mock import patch
import respx
import httpx

from threads_sdk.auth import Credentials, Auth
from threads_sdk.exceptions import AuthenticationError


def test_credentials_creation():
    creds = Credentials(
        access_token="test_token_123",
        user_id="12345",
    )
    assert creds.access_token == "test_token_123"
    assert creds.user_id == "12345"
    assert creds.is_expired is False


def test_credentials_to_json():
    creds = Credentials(access_token="token", user_id="123")
    data = json.loads(creds.to_json())
    assert data["access_token"] == "token"
    assert data["user_id"] == "123"


def test_credentials_from_json():
    json_str = '{"access_token": "token", "user_id": "123"}'
    creds = Credentials.from_json(json_str)
    assert creds.access_token == "token"
    assert creds.user_id == "123"


def test_credentials_save_and_load(tmp_path):
    creds = Credentials(access_token="saved_token", user_id="456")
    file_path = tmp_path / "creds.json"
    creds.save(file_path)

    loaded = Credentials.load(file_path)
    assert loaded.access_token == "saved_token"
    assert loaded.user_id == "456"


def test_auth_get_authorization_url():
    auth = Auth(
        client_id="my_app_id",
        redirect_uri="https://example.com/callback",
    )
    url = auth.get_authorization_url(state="random_state")
    assert "threads.net" in url
    assert "client_id=my_app_id" in url
    assert "redirect_uri=" in url
    assert "state=random_state" in url


@respx.mock
def test_auth_exchange_code_for_token():
    respx.post("https://graph.threads.net/oauth/access_token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "short_token",
            "user_id": "12345",
        })
    )
    auth = Auth(client_id="app_id", client_secret="app_secret", redirect_uri="https://example.com/callback")
    creds = auth.exchange_code("auth_code_123")
    assert creds.access_token == "short_token"
    assert creds.user_id == "12345"


@respx.mock
def test_auth_exchange_code_fails():
    respx.post("https://graph.threads.net/oauth/access_token").mock(
        return_value=httpx.Response(400, json={
            "error": {"message": "Invalid code", "type": "OAuthException"}
        })
    )
    auth = Auth(client_id="app_id", client_secret="app_secret", redirect_uri="https://example.com/callback")
    with pytest.raises(AuthenticationError, match="Invalid code"):
        auth.exchange_code("bad_code")


@respx.mock
def test_auth_get_long_lived_token():
    respx.get("https://graph.threads.net/oauth/access_token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "long_token",
            "token_type": "bearer",
            "expires_in": 5184000,
        })
    )
    auth = Auth(client_id="app_id", client_secret="app_secret")
    result = auth.get_long_lived_token("short_token")
    assert result.access_token == "long_token"
    assert result.expires_in == 5184000


@respx.mock
def test_auth_refresh_token():
    respx.get("https://graph.threads.net/refresh_access_token").mock(
        return_value=httpx.Response(200, json={
            "access_token": "refreshed_token",
            "token_type": "bearer",
            "expires_in": 5184000,
        })
    )
    auth = Auth(client_id="app_id", client_secret="app_secret")
    result = auth.refresh_token("old_long_token")
    assert result.access_token == "refreshed_token"
