"""Part 6 starter: add controlled file tools to the Part 5 agent."""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI


MODEL = "gpt-oss:20b"
BASE_URL = "http://localhost:11434/v1"
MAX_STEPS = 10
MAX_TOOL_CALLS_PER_TURN = 4
MAX_TOTAL_TOOL_CALLS = 12
MAX_WRITES_PER_RUN = 3
MAX_FILE_BYTES = 100_000
MAX_WRITE_CHARACTERS = 50_000
MAX_LISTED_ITEMS = 100
ALLOWED_TEXT_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv"}
WORKSPACE_ROOT = (Path(__file__).resolve().parent / "agent_workspace").resolve()

WriteApprover = Callable[[Path, str], bool]


@dataclass
class RunState:
    total_tool_calls: int = 0
    successful_writes: int = 0


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


# Build these three helpers, then expose them as tools below.
def resolve_safe_path(relative_path: str, root: Path = WORKSPACE_ROOT) -> Path:
    """TODO: Resolve relative_path and reject anything outside root."""
    raise NotImplementedError("Complete resolve_safe_path in Part 6.")


def list_files(path: str = ".", root: Path = WORKSPACE_ROOT) -> str:
    """TODO: List permitted workspace files without leaving root."""
    raise NotImplementedError("Complete list_files in Part 6.")


def read_text_file(path: str, root: Path = WORKSPACE_ROOT) -> str:
    """TODO: Read a small, allowed UTF-8 file from the workspace."""
    raise NotImplementedError("Complete read_text_file in Part 6.")


def write_text_file(
    path: str,
    content: str,
    root: Path,
    approve_write: WriteApprover,
    state: RunState,
) -> str:
    """TODO: Validate, request approval, and then write the text file."""
    raise NotImplementedError("Complete write_text_file in Part 6.")


def deny_writes(_path: Path, _content: str) -> bool:
    return False


def prompt_for_write_approval(path: Path, content: str) -> bool:
    preview_limit = 500
    preview = content[:preview_limit]
    print(f"\nProposed write: {path}")
    print(f"Total proposed length: {len(content):,} characters")
    if len(content) > preview_limit:
        print(f"Preview is truncated to the first {preview_limit:,} characters.")
    print(preview)
    answer = input("Approve this write? [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Read the current local time from this computer.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
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
    # TODO: Add schemas for list_files, read_text_file, and write_text_file.
]


REQUIRED_ARGUMENTS: dict[str, dict[str, str]] = {
    "get_current_time": {},
    "calculate": {"a": "number", "b": "number", "operation": "string"},
    "count_words": {"text": "string"},
    # TODO: Add required arguments for the three file tools.
}

OPTIONAL_ARGUMENTS: dict[str, dict[str, str]] = {
    "get_current_time": {},
    "calculate": {},
    "count_words": {},
    # TODO: Allow an optional path for list_files.
}


def validate_arguments(name: str, arguments: Any) -> dict[str, Any]:
    if name not in REQUIRED_ARGUMENTS:
        raise ValueError(f"Unknown tool: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a JSON object.")
    required = REQUIRED_ARGUMENTS[name]
    allowed = {**required, **OPTIONAL_ARGUMENTS[name]}
    missing = sorted(set(required) - set(arguments))
    unexpected = sorted(set(arguments) - set(allowed))
    if missing:
        raise ValueError(f"Missing argument(s): {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"Unexpected argument(s): {', '.join(unexpected)}")
    for argument_name, value in arguments.items():
        rule = allowed[argument_name]
        if rule == "number":
            is_valid = not isinstance(value, bool) and isinstance(value, (int, float))
        else:
            is_valid = isinstance(value, str)
        if not is_valid:
            raise ValueError(f"{argument_name} must be a JSON {rule}.")
    return arguments


def build_tool_dispatch(
    root: Path,
    approve_write: WriteApprover,
    state: RunState,
) -> dict[str, Callable[..., str]]:
    return {
        "get_current_time": get_current_time,
        "calculate": calculate,
        "count_words": count_words,
        # TODO: Add only the three approved file functions. Do not add a shell.
    }


def run_tool_safely(
    name: str,
    raw_arguments: str,
    root: Path = WORKSPACE_ROOT,
    approve_write: WriteApprover = deny_writes,
    state: RunState | None = None,
) -> str:
    try:
        if state is None:
            state = RunState()
        arguments = json.loads(raw_arguments or "{}")
        validated = validate_arguments(name, arguments)
        dispatch = build_tool_dispatch(root.resolve(), approve_write, state)
        result = dispatch[name](**validated)
        payload = {"ok": True, "result": result}
    except json.JSONDecodeError:
        payload = {"ok": False, "error": "Tool arguments were not valid JSON."}
    except (OSError, PermissionError, TypeError, ValueError) as error:
        payload = {"ok": False, "error": str(error)}
    except Exception:
        payload = {"ok": False, "error": "The tool failed unexpectedly."}
    return json.dumps(payload, ensure_ascii=False)


def run_agent(
    user_message: str,
    client: OpenAI,
    root: Path = WORKSPACE_ROOT,
    approve_write: WriteApprover = deny_writes,
) -> str:
    state = RunState()
    messages: list[Any] = [
        {
            "role": "system",
            "content": "Use only the provided tools. Never invent a successful tool result.",
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

        # TODO: Stop if this turn or this run would exceed the tool-call limits.
        for tool_call in message.tool_calls:
            state.total_tool_calls += 1
            result = run_tool_safely(
                tool_call.function.name,
                tool_call.function.arguments,
                root,
                approve_write,
                state,
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
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    client = OpenAI(base_url=BASE_URL, api_key="ollama")
    prompt = input("You: ").strip()
    if prompt:
        answer = run_agent(
            prompt,
            client,
            WORKSPACE_ROOT,
            prompt_for_write_approval,
        )
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    main()
