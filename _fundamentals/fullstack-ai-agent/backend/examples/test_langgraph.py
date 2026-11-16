
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.hospital_agent import hospital_agent


def main():
    question = (
        "Find cardiology doctors and show "
        "their available appointment slots."
    )

    result = hospital_agent.invoke(
        {
            "messages": [
                HumanMessage(content=question)
            ]
        },
        config={"recursion_limit": 20},
    )

    print("\n=== EXECUTION HISTORY ===")

    for message in result["messages"]:
        print("\nMessage type:", message.type)

        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                print("Selected tool:", call["name"])
                print("Arguments:", call["args"])

        elif message.type == "tool":
            print("Tool result:", message.content)

        elif message.content:
            print("Content:", message.content)

    print("\n=== FINAL ANSWER ===")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
