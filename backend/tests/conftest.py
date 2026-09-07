import pytest
from fastapi.testclient import TestClient

from pushform.app import create_app


@pytest.fixture
def client() -> TestClient:
    with TestClient(create_app()) as test_client:
        yield test_client
