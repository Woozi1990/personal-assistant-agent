import logging
from collections.abc import Callable

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

logger = logging.getLogger(__name__)


class ToolCallingMiddleware(AgentMiddleware):
    async def awrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest], ToolMessage | Command]
    ) -> ToolMessage | Command:
        tool_call = request.tool_call

        try:
            return await handler(request)

        except (RuntimeError, TimeoutError, ConnectionError):
            logger.exception(
                "Tool execution failed: %s", tool_call["name"]
            )

            return ToolMessage(
                content=(
                    "Tool execution failed due to an external service error. "
                    "The operation was not confirmed successful. "
                    "Inform the user and do not claim it succeeded."
                ),
                tool_call_id=tool_call["id"],
                status="error"
            )
