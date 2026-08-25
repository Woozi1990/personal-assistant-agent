
import traceback

from agent.agent import Agent


def main():
    agent = Agent()

    print("Personal Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("> ").strip()
        if not user_input:
            continue
        if user_input in {"exit", "quit"}:
            break
        try:
            response =  agent.invoke(user_input)
            print(f"Assistant: {response}")
        except Exception as e:
            traceback.print_exc()


if __name__ == '__main__':
    main()
