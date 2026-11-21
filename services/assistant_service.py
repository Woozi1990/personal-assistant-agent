from agent.agent import Agent
from agent.confirmation import Confirmation


class AssistantService:
    def __init__(self):
        self._agent = Agent()
        self._confirmation = Confirmation()

    async def chat(self, message, thread_id):
        # 检查当前conversion是否在等待HITL
        if await self._agent.is_interrupted(thread_id):
            pending_action = await self._agent.get_pending_action(thread_id)
            if pending_action is None:
                raise RuntimeError(
                    "Agent is interrupted but no pending action was found"
                )

            decision = (
                await self._confirmation.invoke(
                    user_input=message,
                    pending_action=pending_action
                )
            ).decision

            print("DEBUG: User message =", message)
            print("DEBUG: Confirmation decision =", decision)

            if decision in ("approve", "reject"):
                response = await self._agent.resume(decision, thread_id)
            else:
                response = await self._agent.resume(
                    decision="reject",
                    thread_id=thread_id,
                    message="The user did not confirm the pending action. "
                            "The pending action has been rejected because the user submitted a separated request. "
                )

                if response["status"] == "completed":
                    response = await self._agent.invoke(message, thread_id)
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
