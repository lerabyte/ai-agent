"""Part 6 solution: a controlled local agent with explicit permissions."""

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
    """Counters that must be shared by every tool call in one agent run."""

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


def resolve_safe_path(relative_path: str, root: Path = WORKSPACE_ROOT) -> Path:
    """Resolve a user/model path and prove that it stays inside root."""
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ValueError("Path must be a non-empty string.")

    supplied = Path(relative_path)
    if supplied.is_absolute():
        raise ValueError("Absolute paths are not allowed.")

    safe_root = root.resolve()
    try:
        candidate = (safe_root / supplied).resolve()
        candidate.relative_to(safe_root)
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError("Path must stay inside the agent workspace.") from error

    return candidate


def require_text_extension(path: Path) -> None:
    if path.suffix.lower() not in ALLOWED_TEXT_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_TEXT_EXTENSIONS))
        raise ValueError(f"Only these text file types are allowed: {allowed}")


def list_files(path: str = ".", root: Path = WORKSPACE_ROOT) -> str:
    """List safe, non-hidden items in one workspace directory."""
    folder = resolve_safe_path(path, root)
    if not folder.exists():
        raise ValueError("That directory does not exist.")
    if not folder.is_dir():
        raise ValueError("The requested path is not a directory.")

    safe_root = root.resolve()
    items: list[str] = []
    for child in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        if child.name.startswith(".") or child.is_symlink():
            continue
        if child.is_dir():
            items.append(f"{child.relative_to(safe_root).as_posix()}/")
        elif child.suffix.lower() in ALLOWED_TEXT_EXTENSIONS:
            items.append(child.relative_to(safe_root).as_posix())
        if len(items) == MAX_LISTED_ITEMS:
            items.append("...more items were omitted")
            break

    return "\n".join(items) if items else "No allowed files found."


def read_text_file(path: str, root: Path = WORKSPACE_ROOT) -> str:
    """Read a small UTF-8 text file from the workspace."""
    target = resolve_safe_path(path, root)
    require_text_extension(target)
    if not target.exists():
        raise ValueError("That file does not exist.")
    if not target.is_file():
        raise ValueError("The requested path is not a file.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"Files larger than {MAX_FILE_BYTES:,} bytes cannot be read.")
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("The file is not valid UTF-8 text.") from error


def write_text_file(
    path: str,
    content: str,
    root: Path,
    approve_write: WriteApprover,
    state: RunState,
) -> str:
    """Write text only after path checks and explicit user approval."""
    target = resolve_safe_path(path, root)
    require_text_extension(target)
    if len(content) > MAX_WRITE_CHARACTERS:
        raise ValueError(
            f"Writes are limited to {MAX_WRITE_CHARACTERS:,} characters."
        )
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError(f"Files larger than {MAX_FILE_BYTES:,} bytes cannot be written.")
    if target.exists() and not target.is_file():
        raise ValueError("The requested path is not a file.")
    if state.successful_writes >= MAX_WRITES_PER_RUN:
        raise PermissionError(
            f"This run has reached its limit of {MAX_WRITES_PER_RUN} successful writes."
        )
    if not approve_write(target, content):
        raise PermissionError("The user did not approve this write.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    state.successful_writes += 1
    relative = target.relative_to(root.resolve()).as_posix()
    return f"Wrote {len(content)} characters to {relative}."


def deny_writes(_path: Path, _content: str) -> bool:
    """Safe default for tests or callers that provide no approval UI."""
    return False


def prompt_for_write_approval(path: Path, content: str) -> bool:
    """Show a short preview and ask the human before changing a file."""
    action = "OVERWRITE" if path.exists() else "CREATE"
    preview_limit = 500
    preview = content[:preview_limit]
    print(f"\n[{action}] {path}")
    print(f"Total proposed length: {len(content):,} characters")
    if len(content) > preview_limit:
        print(f"--- truncated preview: first {preview_limit:,} characters ---")
    else:
        print("--- full content preview ---")
    print(preview)
    if len(content) > preview_limit:
        print(f"--- preview truncated; {len(content) - preview_limit:,} characters not shown ---")
    else:
        print("--- end full preview ---")
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
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List allowed files and folders inside the agent workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "A workspace-relative directory, or . for the root.",
                    }
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": "Read an allowed UTF-8 text file inside the agent workspace.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_text_file",
            "description": (
                "Create or replace an allowed text file. "
                "Python asks the user for approval before writing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
        },
    },
]


REQUIRED_ARGUMENTS: dict[str, dict[str, str]] = {
    "get_current_time": {},
    "calculate": {"a": "number", "b": "number", "operation": "string"},
    "count_words": {"text": "string"},
    "list_files": {},
    "read_text_file": {"path": "string"},
    "write_text_file": {"path": "string", "content": "string"},
}

OPTIONAL_ARGUMENTS: dict[str, dict[str, str]] = {
    "get_current_time": {},
    "calculate": {},
    "count_words": {},
    "list_files": {"path": "string"},
    "read_text_file": {},
    "write_text_file": {},
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
    """Create the exact allowlist of functions this run may execute."""
    return {
        "get_current_time": get_current_time,
        "calculate": calculate,
        "count_words": count_words,
        "list_files": lambda path=".": list_files(path, root),
        "read_text_file": lambda path: read_text_file(path, root),
        "write_text_file": lambda path, content: write_text_file(
            path, content, root, approve_write, state
        ),
    }


def run_tool_safely(
    name: str,
    raw_arguments: str,
    root: Path = WORKSPACE_ROOT,
    approve_write: WriteApprover = deny_writes,
    state: RunState | None = None,
) -> str:
    """Validate and run one allowed tool, always returning JSON."""
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
            "content": (
                "You are a careful local assistant. Use only the provided tools. "
                "Never claim that a file action succeeded unless its tool result says ok is true. "
                "If a tool reports an error or denied permission, explain it or choose a "
                "permitted action."
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

        tool_call_count = len(message.tool_calls)
        if tool_call_count > MAX_TOOL_CALLS_PER_TURN:
            return (
                f"Stopped: the model requested {tool_call_count} tools in one turn, "
                f"but the limit is {MAX_TOOL_CALLS_PER_TURN}."
            )
        if state.total_tool_calls + tool_call_count > MAX_TOTAL_TOOL_CALLS:
            return (
                f"Stopped before exceeding the total limit of "
                f"{MAX_TOTAL_TOOL_CALLS} tool calls."
            )

        state.total_tool_calls += tool_call_count
        for tool_call in message.tool_calls:
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
    print(f"Controlled workspace: {WORKSPACE_ROOT}")
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
