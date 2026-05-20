import pytest
from threads_sdk.exceptions import (
    ThreadsError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
)


def test_threads_error_is_base_exception():
    err = ThreadsError("something broke")
    assert isinstance(err, Exception)
    assert str(err) == "something broke"


def test_authentication_error_inherits_threads_error():
    err = AuthenticationError("bad token")
    assert isinstance(err, ThreadsError)
    assert str(err) == "bad token"


def test_rate_limit_error_has_retry_after():
    err = RateLimitError("rate limited", retry_after=60)
    assert isinstance(err, ThreadsError)
    assert err.retry_after == 60


def test_not_found_error_inherits_threads_error():
    err = NotFoundError("post not found")
    assert isinstance(err, ThreadsError)


def test_validation_error_inherits_threads_error():
    err = ValidationError("invalid field")
    assert isinstance(err, ThreadsError)
