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

from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_MODEL, AZURE_OPENAI_BASE_URL


class Agent:
    def __init__(self):
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
            thread_id: str = "default"
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
                "interrupts": interrupts
            }

        final_message = result["messages"][-1]
        return {
            "status": "completed",
            "message": final_message.content
        }

    async def resume(
            self,
            decision: str,
            message: str | None = None,
            thread_id: str = "default"
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
                    "message": (
                        "The user explicitly rejected this action. "
                        "Treat the action as cancelled. "
                        "Do not retry it or ask for confirmation again. "
                        "Simply acknowledge the cancellation."
                    ),
                }]
            }
        elif decision == "respond":
            resume_data = {
                "decisions": [{
                    "type": "respond",
                    "message": message or "The user did not make an approval or rejection decision for this action. Do not execute it."
                }]
            }
        else:
            raise ValueError(f"Unsupported decision: {decision}")

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
            }

        return {
            "status": "completed",
            "message": result["messages"][-1].content,
        }
