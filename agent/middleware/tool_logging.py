from collections.abc import Callable

from langchain.agents.middleware import wrap_tool_call
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

@wrap_tool_call
def tool_logging(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command]
) -> ToolMessage | Command:
    tool_call = request.tool_call

    print(f"Tool: {tool_call['name']}")
    print(f"Arguments: {tool_call['args']}")

    result = handler(request)
    print(f"Result: {result}")
    return result
