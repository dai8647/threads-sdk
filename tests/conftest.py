import pytest
from threads_sdk.auth import Credentials


@pytest.fixture
def mock_credentials():
    return Credentials(access_token="test_token_123", user_id="12345")
