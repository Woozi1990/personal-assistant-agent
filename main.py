import asyncio

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agent.agent import Agent


async def main():
    agent = Agent()

    config = {
        "configurable": {
            "thread_id": "main"
        }
    }
    waiting_for_confirmation = False

    print("Personal Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input in {"exit", "quit"}:
            break

        if waiting_for_confirmation:
            graph_input = Command(
                resume=user_input
            )
        else:
            graph_input = {
                "messages":[
                    HumanMessage(content=user_input)
                ]
            }

        try:
            result = await agent.graph.ainvoke(
                graph_input,
                config=config
            )
            if result.get("__interrupt__"):
                waiting_for_confirmation = True
                interrupt_info = result["__interrupt__"][0]

                print(f"Confirmation required: {interrupt_info.value}")

            else:
                waiting_for_confirmation = False

                final_message = result["messages"][-1]
                print(f"Assistant: {final_message.content}")

            # for message in result["messages"]:
            #     print(type(message).__name__)
            #     print(message)
            #     print("=" * 50)



        except Exception as exc:
            print(f"Error: {exc}\n")


if __name__ == '__main__':
    asyncio.run(main())
