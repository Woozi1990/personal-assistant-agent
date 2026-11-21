from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

import pytest

from services.assistant_service import AssistantService


PENDING_ACTION = {
    "name": "send_email",
    "args": {"draft_id": "draft-A"},
}


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
        agent.get_pending_action = AsyncMock(return_value=PENDING_ACTION)
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

    agent.get_pending_action.assert_not_awaited()
    confirmation.invoke.assert_not_awaited()


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

    agent.get_pending_action.assert_awaited_once_with("test-001")
    confirmation.invoke.assert_awaited_once_with(
        user_input="是的",
        pending_action=PENDING_ACTION,
    )


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

    agent.get_pending_action.assert_awaited_once_with("test-001")
    confirmation.invoke.assert_awaited_once_with(
        user_input="不要删除",
        pending_action=PENDING_ACTION,
    )


@pytest.mark.asyncio
async def test_unrelated_request(service):
    assistant, agent, confirmation = service
    agent.is_interrupted.return_value = True
    confirmation.invoke.return_value = SimpleNamespace(
        decision="other"
    )

    agent.resume.return_value = {
        "status": "completed",
        "message": "已取消之前的操作"
    }

    agent.invoke.return_value = {
        "status": "completed",
        "message":"明天没有安排"
    }

    result = await assistant.chat("明天有什么安排", "test-001")

    assert result["status"] == "completed"
    agent.resume.assert_awaited_once()
    assert agent.resume.await_args.kwargs["decision"] == "reject"
    assert agent.resume.await_args.kwargs["thread_id"] == "test-001"

    agent.invoke.assert_awaited_once_with("明天有什么安排", "test-001")

    agent.get_pending_action.assert_awaited_once_with("test-001")
    confirmation.invoke.assert_awaited_once_with(
        user_input="明天有什么安排",
        pending_action=PENDING_ACTION,
    )


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

    agent.get_pending_action.assert_not_awaited()
    confirmation.invoke.assert_not_awaited()


@pytest.mark.asyncio
async def test_resume_interrupted(service):
    assistant, agent, confirmation = service

    agent.is_interrupted.return_value = True
    confirmation.invoke.return_value = SimpleNamespace(
        decision="other"
    )

    interrupt = SimpleNamespace(
        value={
            "action_requests": [
                {
                    "name": "send_email",
                    "args": {"draft_id": "draft-123"},
                }
            ]
        }
    )

    messages = ["previous messages"]

    agent.resume.return_value = {
        "status": "interrupted",
        "interrupts": [interrupt],
        "messages": messages,
    }

    confirmation.format_message.return_value = (
        "确定要发送邮件吗？"
    )

    result = await assistant.chat(
        "Alice的电话是多少",
        "test-001",
    )

    assert result == {
        "status": "pending",
        "message": "确定要发送邮件吗？",
    }

    # 旧操作仍处于中断状态，不能处理新请求
    agent.invoke.assert_not_awaited()

    confirmation.format_message.assert_awaited_once_with(
        messages,
        "send_email",
        {"draft_id": "draft-123"},
    )

    agent.get_pending_action.assert_awaited_once_with("test-001")
    confirmation.invoke.assert_awaited_once_with(
        user_input="Alice的电话是多少",
        pending_action=PENDING_ACTION,
    )


@pytest.mark.asyncio
async def test_unrelated_request_new_interrupt(service):
    assistant, agent, confirmation = service

    agent.is_interrupted.return_value = True
    confirmation.invoke.return_value = SimpleNamespace(
        decision="other"
    )

    # 邮件 A 被拒绝，旧 HITL 正常结束
    agent.resume.return_value = {
        "status": "completed",
        "message": "已取消邮件 A",
    }

    # 处理邮件 B 时产生新的 HITL
    interrupt = SimpleNamespace(
        value={
            "action_requests": [
                {
                    "name": "send_email",
                    "args": {"draft_id": "draft-B"},
                }
            ]
        }
    )

    messages = ["messages for email B"]

    agent.invoke.return_value = {
        "status": "interrupted",
        "interrupts": [interrupt],
        "messages": messages,
    }

    confirmation.format_message.return_value = (
        "确定要发送邮件 B 吗？"
    )

    result = await assistant.chat(
        "给Alice发送另一封邮件",
        "test-001",
    )

    assert result == {
        "status": "pending",
        "message": "确定要发送邮件 B 吗？",
    }

    agent.resume.assert_awaited_once()
    assert agent.resume.await_args.kwargs["decision"] == "reject"

    agent.invoke.assert_awaited_once_with(
        "给Alice发送另一封邮件",
        "test-001",
    )

    confirmation.format_message.assert_awaited_once_with(
        messages,
        "send_email",
        {"draft_id": "draft-B"},
    )

    agent.get_pending_action.assert_awaited_once_with("test-001")
    confirmation.invoke.assert_awaited_once_with(
        user_input="给Alice发送另一封邮件",
        pending_action=PENDING_ACTION,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pending_action",
    [
        {"name": "send_email", "args": {"draft_id": "draft-123"}},
        {"name": "delete_event", "args": {"event_id": "event-123"}},
        {"name": "delete_contact", "args": {"contact_id": "contact-123"}},
    ],
    ids=["send_email", "delete_event", "delete_contact"],
)
async def test_pending_action_passed_to_confirmation(service, pending_action):
    assistant, agent, confirmation = service
    agent.is_interrupted.return_value = True
    agent.get_pending_action.return_value = pending_action
    confirmation.invoke.return_value = SimpleNamespace(decision="reject")
    agent.resume.return_value = {
        "status": "completed",
        "message": "操作已取消",
    }

    result = await assistant.chat("取消", "test-001")

    assert result == {"status": "completed", "message": "操作已取消"}
    agent.get_pending_action.assert_awaited_once_with("test-001")
    confirmation.invoke.assert_awaited_once_with(
        user_input="取消",
        pending_action=pending_action,
    )
    agent.resume.assert_awaited_once_with("reject", "test-001")
    agent.invoke.assert_not_awaited()
