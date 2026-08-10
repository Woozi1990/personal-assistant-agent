import asyncio

from langchain_core.messages import HumanMessage

from agent.agent import Agent


async def main():
    agent_builder = Agent()
    print("Personal Assistant")
    print("Type 'exit' to stop.\n")

    messages = []
    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input in {"exit", "quit"}:
            break

        decision = agent_builder.classify_pending_action(user_input)
        allowed_tool_names = None
        if decision is not None:
            if decision.decision == "confirm":
                pending_action = agent_builder.get_pending_action()

                if pending_action is not None:
                    allowed_tool_names = [pending_action.action]
            elif decision.decision == "cancel":
                agent_builder.clear_pending_action()
                print("Assistant: 已取消当前待确认的操作。")
                continue
            elif decision.decision == "modify":
                allowed_tool_names = ["update_draft"]
            elif decision.decision == "other":
                pass

        messages.append(HumanMessage(content=user_input))

        agent = agent_builder.build_agent(
            messages,
            allowed_tool_names=allowed_tool_names,
        )
        try:
            result = await agent.ainvoke({
                "messages": messages,
            })
            messages = result["messages"]
            final_message = messages[-1]

            for message in result["messages"]:
                print(type(message).__name__)
                print(message)
                print("=" * 50)

            print(f"Assistant: {final_message.content}")

        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == '__main__':
    asyncio.run(main())
