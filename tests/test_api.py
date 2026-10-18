from unittest.mock import patch, AsyncMock

import pytest
from starlette.testclient import TestClient

from api.main import app


@pytest.fixture
def mock_assistant():
    with patch("api.main.AssistantService") as mock_class:
        assistant = mock_class.return_value
        assistant.chat = AsyncMock()

        with TestClient(app) as client:
            yield client, assistant


def test_health(mock_assistant):
    client, _ = mock_assistant
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_success(mock_assistant):
    client, assistant = mock_assistant

    assistant.chat.return_value = {
        "status":"completed",
        "message":"明天没有安排"
    }

    response = client.post(
        "/chat",
        json={
            "session_id":"test-001",
            "message":"明天有什么安排"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id":"test-001",
        "status":"completed",
        "message":"明天没有安排"
    }

    assistant.chat.assert_awaited_once_with(
        message="明天有什么安排",
        thread_id="test-001"
    )

def test_chat_validation_error(mock_assistant):
    client, assistant = mock_assistant

    response = client.post(
        "/chat",
        json={
            "session_id":"",
            "message":""
        }
    )

    assert response.status_code == 422
    assistant.chat.assert_not_awaited()

def test_chat_internal_error(mock_assistant):
    client, assistant = mock_assistant

    assistant.chat.side_effect = RuntimeError("Test error")

    response = client.post(
        "/chat",
        json={
            "session_id":"test-001",
            "message":"明天有什么安排"
        }
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
    }