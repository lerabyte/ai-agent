"""Part 3 starter: the Part 2 flow before it becomes a loop."""

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
            "content": "What time is it on this computer right now? Use the available tool.",
        }
    ]

    first_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )
    assistant_message = first_response.choices[0].message
    messages.append(assistant_message.model_dump(exclude_none=True))

    if not assistant_message.tool_calls:
        print(assistant_message.content or "The model returned no answer or tool call.")
        return
    if len(assistant_message.tool_calls) != 1:
        raise ValueError("The starter handles exactly one tool call")

    tool_call = assistant_message.tool_calls[0]
    function_name = tool_call.function.name
    function_arguments = json.loads(tool_call.function.arguments or "{}")

    if function_name != "get_current_time":
        raise ValueError(f"Unknown tool requested: {function_name}")
    if function_arguments:
        raise ValueError("get_current_time does not accept arguments")

    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": get_current_time(),
        }
    )

    final_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )
    final_answer = final_response.choices[0].message.content
    print(final_answer or "The model returned no final text.")

    # TODO: Replace the fixed first/second request with a loop that continues
    # until the model returns a response with no tool calls.


if __name__ == "__main__":
    main()
