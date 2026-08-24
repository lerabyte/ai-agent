"""Part 3 solution: keep using tools until the model gives a final answer."""

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


def run_tool(function_name: str, arguments_json: str) -> str:
    """Run one allowed tool and return its result as text."""
    arguments = json.loads(arguments_json or "{}")

    if function_name == "get_current_time":
        if arguments:
            return "Error: get_current_time does not accept arguments."
        return get_current_time()

    return f"Error: the tool '{function_name}' is not available."


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

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        assistant_message = response.choices[0].message
        messages.append(assistant_message.model_dump(exclude_none=True))

        if not assistant_message.tool_calls:
            print(assistant_message.content or "The model returned no final text.")
            break

        for tool_call in assistant_message.tool_calls:
            tool_result = run_tool(
                tool_call.function.name,
                tool_call.function.arguments,
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )


if __name__ == "__main__":
    main()
