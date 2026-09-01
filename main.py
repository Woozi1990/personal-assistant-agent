import traceback

from agent.agent import Agent
from agent.confirmation import Confirmation


def main():
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

        response = agent.invoke(user_input)
        if response["status"] == "interrupted":
            interrupt = response["interrupts"][0]
            request = interrupt.value["action_requests"][0]

            print()
            print("需要确认以下操作：")
            print(f"Tool: {request['name']}")
            print(f"Arguments: {request['args']}")

            user_response = input("确认执行？(y/n): ").strip()
            decision = confirmation.invoke(user_response).decision
            print(f"Decision: {decision}")

            if decision == "approve":
                response = agent.resume("approve")
            elif decision == "reject":
                response = agent.resume("reject")
            else:
                agent.resume(
                    decision="respond",
                    message="The user did not answer the pending confirmation. "
                            "The current input is a separate request. "
                            "Do not execute or treat the pending action as rejected."
                )
                response = agent.invoke(user_response)

        print(f"Assistant: {response['message']}")


if __name__ == '__main__':
    main()
