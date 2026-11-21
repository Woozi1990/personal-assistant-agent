from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from agent.build_tools import build_tools
from agent.middleware.tool_logging import ToolCallingMiddleware
from agent.prompt import dynamic_system_prompt

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_MODEL, AZURE_OPENAI_BASE_URL, require_config


class Agent:
    def __init__(self):
        require_config(
            AZURE_OPENAI_API_KEY=AZURE_OPENAI_API_KEY,
            AZURE_OPENAI_BASE_URL=AZURE_OPENAI_BASE_URL,
            AZURE_OPENAI_MODEL=AZURE_OPENAI_MODEL,
        )
        self._llm = ChatOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            base_url=AZURE_OPENAI_BASE_URL,
            model=AZURE_OPENAI_MODEL,
            temperature=0.0,
        )
        self._tools = build_tools()
        self._checkpointer = InMemorySaver()

        self._agent = create_agent(
            model=self._llm,
            tools=self._tools,
            middleware=[
                dynamic_system_prompt,
                ToolCallingMiddleware(),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "delete_event": True,
                        "delete_contact": True,
                        "send_email": True,
                    }
                )
            ],
            checkpointer=self._checkpointer,
        )

    async def invoke(
            self,
            user_input: str,
            thread_id: str
    ):
        result = await self._agent.ainvoke(
            {
                "messages":
                    [
                        HumanMessage(content=user_input)
                    ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        if "__interrupt__" in result:
            interrupts = result["__interrupt__"]
            return {
                "status": "interrupted",
                "interrupts": interrupts,
                "messages": result["messages"]
            }

        final_message = result["messages"][-1]
        return {
            "status": "completed",
            "message": final_message.content
        }

    async def resume(
            self,
            decision: str,
            thread_id: str,
            message: str | None = None,
    ):

        if decision == "approve":
            resume_data = {
                "decisions": [{
                    "type": "approve",
                }]
            }
        elif decision == "reject":
            resume_data = {
                "decisions": [{
                    "type": "reject",
                    "message": message or (
                        "The user explicitly rejected this action. "
                        "Treat the action as cancelled. "
                        "Do not retry it or ask for confirmation again. "
                        "Simply acknowledge the cancellation."
                    ),
                }]
            }
        else:
            raise ValueError(f"Unsupported decision: {decision}")

        print("DEBUG: Agent.resume decision =", decision)
        print("DEBUG: resume_data =", resume_data)

        result = await self._agent.ainvoke(
            Command(resume=resume_data),
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        if "__interrupt__" in result:
            return {
                "status": "interrupted",
                "interrupts": result["__interrupt__"],
                "messages": result["messages"]
            }

        return {
            "status": "completed",
            "message": result["messages"][-1].content,
        }

    async def is_interrupted(self, thread_id: str):
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        state = await self._agent.aget_state(config)
        return bool(state.interrupts)

    async def get_pending_action(self, thread_id: str) -> dict | None:
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        state = await self._agent.aget_state(config)

        if not state.interrupts:
            return None

        interrupt = state.interrupts[0]

        action_requests = interrupt.value.get("action_requests", [])

        if not action_requests:
            return None

        return action_requests[0]
