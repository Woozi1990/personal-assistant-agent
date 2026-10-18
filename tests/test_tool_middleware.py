from unittest.mock import AsyncMock, Mock

import pytest
from langchain_core.messages import ToolMessage

from agent.middleware.tool_logging import ToolCallingMiddleware


@pytest.fixture
def middleware():
    return ToolCallingMiddleware()


@pytest.fixture
def tool_request():
    request = Mock()
    request.tool_call = {
        "id": "call-123",
        "name": "list_events",
        "args": {},
    }
    return request


@pytest.mark.asyncio
async def test_tool_success(middleware, tool_request):
    expected = ToolMessage(
        content="Success",
        tool_call_id="call-123",
    )

    handler = AsyncMock(return_value=expected)

    result = await middleware.awrap_tool_call(tool_request, handler)

    assert result is expected
    handler.assert_awaited_once_with(tool_request)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("API error"),
        TimeoutError("Request timeout"),
        ConnectionError("Connection failed"),
    ],
)
async def test_tool_external_error(middleware, tool_request, error):
    handler = AsyncMock(side_effect=error)

    result = await middleware.awrap_tool_call(tool_request, handler)

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert result.tool_call_id == "call-123"
    assert "not confirmed successful" in result.content


@pytest.mark.asyncio
async def test_unexpected_error_propagates(middleware, tool_request):
    handler = AsyncMock(side_effect=ValueError("Unexpected error"))

    with pytest.raises(ValueError):
        await middleware.awrap_tool_call(tool_request, handler)