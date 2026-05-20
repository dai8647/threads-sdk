import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from threads_sdk.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_post_text(runner):
    mock_client = MagicMock()
    mock_client.create_text_post.return_value = MagicMock(id="post_001")
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("threads_sdk.cli.ThreadsClient", return_value=mock_client):
        with patch("threads_sdk.cli.Credentials") as mock_creds:
            mock_creds.load.return_value = MagicMock(access_token="tok", user_id="123")
            result = runner.invoke(main, ["post", "Hello from CLI"])
            assert result.exit_code == 0
            assert "post_001" in result.output


def test_cli_posts_list(runner):
    mock_client = MagicMock()
    mock_client.get_user_posts.return_value = [
        MagicMock(id="p1", text="Post 1", media_type="TEXT", timestamp="2026-05-20"),
        MagicMock(id="p2", text="Post 2", media_type="IMAGE", timestamp="2026-05-20"),
    ]
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with patch("threads_sdk.cli.ThreadsClient", return_value=mock_client):
        with patch("threads_sdk.cli.Credentials") as mock_creds:
            mock_creds.load.return_value = MagicMock(access_token="tok", user_id="123")
            result = runner.invoke(main, ["posts"])
            assert result.exit_code == 0
            assert "Post 1" in result.output


def test_cli_auth_no_credentials(runner):
    with patch("threads_sdk.cli.Credentials") as mock_creds:
        mock_creds.load.side_effect = FileNotFoundError()
        result = runner.invoke(main, ["post", "test"])
        assert result.exit_code != 0 or "credentials" in result.output.lower() or "not found" in result.output.lower()
