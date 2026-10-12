from agent.agent import Agent
from agent.confirmation import Confirmation


class AssistantService:
    def __init__(self):
        self._agent = Agent()
        self._confirmation = Confirmation()

    async def chat(self, message, thread_id):
        # 检查当前conversion是否在等待HITL
        if await self._agent.is_interrupted(thread_id):
            decision = (await self._confirmation.invoke(message)).decision
            if decision in ("approve", "reject"):
                return await self._agent.resume(decision, thread_id)
            else:
                await self._agent.resume(
                    decision="respond",
                    thread_id=thread_id,
                    message="The user did not answer the pending confirmation. "
                            "The current input is a separate request. "
                            "Do not execute or treat the pending action as rejected."
                )
                return await self._agent.invoke(message, thread_id)
        else:
            response = await self._agent.invoke(message, thread_id)
            # 如果请求需要用户确认
            if response["status"] == "interrupted":
                interrupt = response["interrupts"][0]
                action_request = interrupt.value["action_requests"][0]
                confirmation_message = await self._confirmation.format_message(
                    response["messages"],
                    action_request["name"],
                    action_request["args"]
                )

                return {
                    "status": "pending",
                    "message": confirmation_message
                }
            return response
