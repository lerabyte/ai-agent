"""Part 4 starter: connect more than one tool to the agent loop."""

import json
import re
from datetime import datetime
from typing import Any, Callable

from openai import OpenAI


MODEL = "gpt-oss:20b"
BASE_URL = "http://localhost:11434/v1"


def get_current_time() -> str:
    """Return the computer's local time."""
    return datetime.now().astimezone().strftime("%I:%M:%S %p %Z")


def calculate(a: float, b: float, operation: str) -> str:
    """Apply one of four clearly allowed arithmetic operations."""
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        result = a / b
    else:
        raise ValueError("Operation must be add, subtract, multiply, or divide.")

    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)


def count_words(text: str) -> str:
    """Count words while keeping contractions and hyphenated words together."""
    words = re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", text, flags=re.UNICODE)
    return str(len(words))


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Read the current local time from this computer.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    # TODO: Describe the calculate tool here.
    # TODO: Describe the count_words tool here.
]


TOOL_DISPATCH: dict[str, Callable[..., str]] = {
    "get_current_time": get_current_time,
    # TODO: Connect "calculate" to calculate.
    # TODO: Connect "count_words" to count_words.
}


def run_tool(name: str, arguments: dict[str, Any]) -> str:
    """Find an approved function by name and run it."""
    function = TOOL_DISPATCH.get(name)
    if function is None:
        raise ValueError(f"Unknown tool: {name}")
    return function(**arguments)


def run_agent(user_message: str, client: OpenAI) -> str:
    """Keep calling the model until it returns text instead of tool calls."""
    messages: list[Any] = [
        {
            "role": "system",
            "content": (
                "Use the available tools whenever they are needed. "
                "Never invent a tool result."
            ),
        },
        {"role": "user", "content": user_message},
    ]

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or "The model returned no text."

        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments or "{}")
            result = run_tool(tool_call.function.name, arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )


def main() -> None:
    client = OpenAI(base_url=BASE_URL, api_key="ollama")
    prompt = input("You: ").strip()
    if prompt:
        print(f"\nAgent: {run_agent(prompt, client)}")


if __name__ == "__main__":
    main()
