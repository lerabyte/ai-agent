"""Part 5 solution: validate tool calls, return errors, and limit the loop."""

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
    if len(text) > 10_000:
        raise ValueError("Text must contain at most 10,000 characters.")
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


ARGUMENT_RULES: dict[str, dict[str, str]] = {
    "get_current_time": {},
    "calculate": {"a": "number", "b": "number", "operation": "string"},
    "count_words": {"text": "string"},
}


def validate_arguments(name: str, arguments: Any) -> dict[str, Any]:
    """Return validated arguments or raise a useful ValueError."""
    if name not in TOOL_DISPATCH:
        raise ValueError(f"Unknown tool: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")

    expected = ARGUMENT_RULES[name]
    missing = sorted(set(expected) - set(arguments))
    unexpected = sorted(set(arguments) - set(expected))

    if missing:
        raise ValueError(f"Missing argument(s): {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"Unexpected argument(s): {', '.join(unexpected)}")

    for argument_name, rule in expected.items():
        value = arguments[argument_name]
        if rule == "number":
            # bool is a subclass of int in Python, so reject it explicitly.
            is_valid = not isinstance(value, bool) and isinstance(value, (int, float))
        else:
            is_valid = isinstance(value, str)
        if not is_valid:
            raise ValueError(f"{argument_name} must be a JSON {rule}.")

    return arguments


def run_tool_safely(name: str, raw_arguments: str) -> str:
    """Run an approved tool and always return a JSON result to the model."""
    try:
        arguments = json.loads(raw_arguments or "{}")
        validated = validate_arguments(name, arguments)
        result = TOOL_DISPATCH[name](**validated)
        payload = {"ok": True, "result": result}
    except json.JSONDecodeError:
        payload = {"ok": False, "error": "Tool arguments were not valid JSON."}
    except (TypeError, ValueError) as error:
        payload = {"ok": False, "error": str(error)}
    except Exception:
        # Unexpected implementation errors stay recoverable without exposing details.
        payload = {"ok": False, "error": "The tool failed unexpectedly."}

    return json.dumps(payload, ensure_ascii=False)


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
