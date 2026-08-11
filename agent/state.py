from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

from agent.pending_action import PendingAction


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    pending_action: PendingAction | None
    requires_confirmation: bool
    selected_tool_names: list[str]
    forced_tool_name:str|None
    confirmation_response: str | None
    confirmation_decision: str | None
