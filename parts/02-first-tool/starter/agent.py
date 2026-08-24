"""Part 2 starter: connect one Python tool to the local model."""

import json
from datetime import datetime

from openai import OpenAI


MODEL = "gpt-oss:20b"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Read the current date and time from this computer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
]


def get_current_time() -> str:
    """Return the computer's current local date and time."""
    now = datetime.now().astimezone()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z")


def main() -> None:
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    messages = [
        {
            "role": "user",
            "content": "What time is it on this computer right now?",
        }
    ]

    # TODO 1: Add "Use the available tool." to the question, then add
    # tools=TOOLS to this request so the model can request get_current_time.
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    assistant_message = response.choices[0].message
    messages.append(assistant_message.model_dump(exclude_none=True))

    if not assistant_message.tool_calls:
        print(assistant_message.content or "The model returned no text.")
        print("\nThe model could not read the clock. Complete TODO 1, then run this again.")
        return

    tool_call = assistant_message.tool_calls[0]

    # TODO 2: Convert the tool's JSON argument text into a Python dictionary.
    arguments: dict[str, object] = {}

    if tool_call.function.name != "get_current_time":
        raise ValueError(f"Unknown tool requested: {tool_call.function.name}")
    if arguments:
        raise ValueError("get_current_time does not accept arguments")

    # TODO 3: Run get_current_time() and store its returned text in result.
    result = "Replace this text with the function result."

    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        }
    )

    # TODO 4: Send messages to the model again with tools=TOOLS.
    final_response = None

    if final_response is None:
        print("Complete TODOs 2–4 to return the tool result to the model.")
        return

    final_answer = final_response.choices[0].message.content
    print(final_answer or "The model returned no final text.")


if __name__ == "__main__":
    main()
