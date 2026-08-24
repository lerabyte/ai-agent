"""Part 5 starter: make tool failures recoverable."""

import json
import re
from datetime import datetime
from typing import Any, Callable

from openai import OpenAI


MODEL = "gpt-oss:20b"
BASE_URL = "http://localhost:11434/v1"
MAX_STEPS = 8


def get_current_time() -> str:
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
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Add, subtract, multiply, or divide two numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"},
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                    },
                },
                "required": ["a", "b", "operation"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_words",
            "description": "Count the words in a piece of text.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
]


TOOL_DISPATCH: dict[str, Callable[..., str]] = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "count_words": count_words,
}


def run_tool_safely(name: str, raw_arguments: str) -> str:
    """Run one tool and return JSON. Add validation and recovery here."""
    # TODO: Reject unknown tool names.
    # TODO: Catch invalid JSON, invalid arguments, and tool errors.
    arguments = json.loads(raw_arguments or "{}")
    result = TOOL_DISPATCH[name](**arguments)
    return json.dumps({"ok": True, "result": result})


def run_agent(user_message: str, client: OpenAI) -> str:
    messages: list[Any] = [
        {
            "role": "system",
            "content": (
                "Use tools when needed. If a tool reports an error, "
                "correct the request or explain the problem."
            ),
        },
        {"role": "user", "content": user_message},
    ]

    # This bounded loop prevents an accidental infinite conversation.
    for _step in range(1, MAX_STEPS + 1):
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
            result = run_tool_safely(
                tool_call.function.name,
                tool_call.function.arguments,
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return f"Stopped after {MAX_STEPS} model turns without a final answer."


def main() -> None:
    client = OpenAI(base_url=BASE_URL, api_key="ollama")
    prompt = input("You: ").strip()
    if prompt:
        print(f"\nAgent: {run_agent(prompt, client)}")


if __name__ == "__main__":
    main()
