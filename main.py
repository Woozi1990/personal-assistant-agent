import asyncio

from agent.agent import Agent
from agent.confirmation import Confirmation


async def main():
    agent = Agent()
    confirmation = Confirmation()

    print("Personal Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input in {"exit", "quit"}:
            break

        response = await agent.invoke(user_input)
        if response["status"] == "interrupted":
            interrupt = response["interrupts"][0]
            request = interrupt.value["action_requests"][0]

            print()
            print("需要确认以下操作：")
            print(f"Tool: {request['name']}")
            print(f"Arguments: {request['args']}")

            user_response = input("请确认或取消该操作: ").strip()
            decision = (await confirmation.invoke(user_response)).decision
            print(f"Decision: {decision}")

            if decision == "approve":
                response = await agent.resume("approve")
            elif decision == "reject":
                response = await agent.resume("reject")
            else:
                await agent.resume(
                    decision="respond",
                    message="The user did not answer the pending confirmation. "
                            "The current input is a separate request. "
                            "Do not execute or treat the pending action as rejected."
                )
                response = await agent.invoke(user_response)

        print(f"Assistant: {response['message']}")


if __name__ == '__main__':
    asyncio.run(main())
