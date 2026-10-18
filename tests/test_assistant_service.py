from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import pytest

from services.assistant_service import AssistantService


@pytest.fixture
def service():
    with(
        patch("services.assistant_service.Agent") as agent_class,
        patch("services.assistant_service.Confirmation") as confirmation_class,
    ):
        assistant = AssistantService()
        agent = agent_class.return_value
        confirmation = confirmation_class.return_value

        agent.is_interrupted = AsyncMock()
        agent.invoke = AsyncMock()
        agent.resume = AsyncMock()

        confirmation.invoke = AsyncMock()
        confirmation.format_message = AsyncMock()

        yield assistant, agent, confirmation


@pytest.mark.asyncio
async def test_normal_request(service):
    assistant, agent, confirmation = service

    agent.is_interrupted.return_value = False
    agent.invoke.return_value = {
        "status": "completed",
        "message": "明天没有安排"
    }

    result = await assistant.chat("明天有什么安排", "test-001")
    assert result["status"] == "completed"
    assert result["message"] == "明天没有安排"

    agent.invoke.assert_awaited_once_with(
        "明天有什么安排",
        "test-001",
    )


@pytest.mark.asyncio
async def test_approve(service):
    assistant, agent, confirmation = service
    agent.is_interrupted.return_value = True
    confirmation.invoke.return_value = SimpleNamespace(
        decision="approve"
    )

    agent.resume.return_value = {
        "status": "completed",
        "message": "已删除会议"
    }

    result = await assistant.chat("是的", "test-001")

    assert result["status"] == "completed"
    agent.resume.assert_awaited_once_with("approve", "test-001")


@pytest.mark.asyncio
async def test_reject(service):
    assistant, agent, confirmation = service
    agent.is_interrupted.return_value = True
    confirmation.invoke.return_value = SimpleNamespace(
        decision="reject"
    )
    agent.resume.return_value = {
        "status": "completed",
        "message": "已取消操作"
    }

    result = await assistant.chat("不要删除", "test-001")

    assert result["status"] == "completed"
    agent.resume.assert_awaited_once_with("reject", "test-001")

@pytest.mark.asyncio
async def test_unrelated_request(service):
    assistant, agent, confirmation = service
    agent.is_interrupted.return_value = True
    confirmation.invoke.return_value = SimpleNamespace(
        decision="other"
    )
    agent.invoke.return_value = {
        "status": "completed",
        "message":"明天没有安排"
    }

    result = await assistant.chat("明天有什么安排", "test-001")

    assert result["status"] == "completed"
    agent.resume.assert_awaited_once()
    assert agent.resume.await_args.kwargs["decision"] == "respond"
    assert agent.resume.await_args.kwargs["thread_id"] == "test-001"

    agent.invoke.assert_awaited_once_with("明天有什么安排", "test-001")

@pytest.mark.asyncio
async def test_pending_confirmation(service):
    assistant, agent, confirmation = service

    agent.is_interrupted.return_value = False

    interrupt = SimpleNamespace(
        value={
            "action_requests":[
                {
                    "name":"delete_event",
                    "args":{"event_id":"event-123"},
                }
            ]
        }
    )

    messages = ["previous messages"]

    agent.invoke.return_value = {
        "status": "interrupted",
        "interrupts": [interrupt],
        "messages": messages,
    }

    confirmation.format_message.return_value = ("确定要删除这个会议吗?")

    result = await assistant.chat("删除这个会议", "test-001")

    assert result == {
        "status":"pending",
        "message":"确定要删除这个会议吗?"
    }

    confirmation.format_message.assert_awaited_once_with(
        messages,
        "delete_event",
        {"event_id":"event-123"},
    )