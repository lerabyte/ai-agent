from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys
import tempfile
import types
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]

PARTS = [
    "01-connect-model",
    "02-first-tool",
    "03-agent-loop",
    "04-multiple-tools",
    "05-error-recovery",
    "06-permissions-and-limits",
]


def solution_tree(part: str) -> ast.Module:
    path = ROOT / "parts" / part / "solution" / "agent.py"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def defined_functions(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def load_solution(part: str) -> Any:
    """Import a solution without making any model or network request."""
    if "openai" not in sys.modules:
        try:
            __import__("openai")
        except ModuleNotFoundError:
            stub = types.ModuleType("openai")
            stub.OpenAI = object
            sys.modules["openai"] = stub

    path = ROOT / "parts" / part / "solution" / "agent.py"
    module_name = f"course_{part.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def assert_raises(error_type: type[BaseException], function: Callable[..., Any], *args: Any) -> None:
    try:
        function(*args)
    except error_type:
        return
    raise AssertionError(f"Expected {error_type.__name__} from {function.__name__}")


def test_every_part_has_all_course_files() -> None:
    for part in PARTS:
        root = ROOT / "parts" / part
        for relative in ["README.md", "challenge.md", "starter/agent.py", "solution/agent.py"]:
            assert (root / relative).is_file(), f"{part} is missing {relative}"


def test_every_python_file_parses() -> None:
    for path in (ROOT / "parts").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_course_adds_expected_capabilities() -> None:
    expected_function_groups = {
        "02-first-tool": [{"get_current_time"}],
        "03-agent-loop": [{"get_current_time", "run_tool"}],
        "04-multiple-tools": [{"calculate", "count_words"}],
        "05-error-recovery": [{"run_agent"}, {"agent_loop"}],
        "06-permissions-and-limits": [{"read_text_file", "write_text_file"}],
    }
    for part, alternatives in expected_function_groups.items():
        names = defined_functions(solution_tree(part))
        assert any(group <= names for group in alternatives), f"{part} functions: {sorted(names)}"

    part_three = solution_tree("03-agent-loop")
    assert any(isinstance(node, ast.While) for node in ast.walk(part_three))


def test_final_solution_does_not_expose_shell_or_dynamic_execution() -> None:
    tree = solution_tree("06-permissions-and-limits")
    forbidden_imports = {"subprocess"}
    imported: set[str] = set()
    imported_names: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                called_names.add(f"{node.func.value.id}.{node.func.attr}")
    assert not (forbidden_imports & imported)
    assert "system" not in imported_names
    assert not ({"eval", "exec", "system", "os.system"} & called_names)


def test_part_four_helpers_run_offline() -> None:
    part = load_solution("04-multiple-tools")
    assert part.calculate(18, 7, "multiply") == "126"
    assert part.calculate(10, 4, "divide") == "2.5"
    assert part.count_words("Agents connect models to useful actions.") == "6"
    assert_raises(ValueError, part.calculate, 1, 0, "divide")
    assert_raises(ValueError, part.calculate, 1, 2, "power")


def test_part_five_returns_structured_errors() -> None:
    part = load_solution("05-error-recovery")

    success = json.loads(
        part.run_tool_safely(
            "calculate",
            '{"a": 18, "b": 7, "operation": "multiply"}',
        )
    )
    assert success == {"ok": True, "result": "126"}

    bad_requests = [
        ("calculate", '{"a": 20, "b": 0, "operation": "divide"}'),
        ("calculate", '{"a": true, "b": 2, "operation": "add"}'),
        ("calculate", '{"a": 1, "operation": "add"}'),
        ("missing_tool", "{}"),
        ("count_words", "{bad json"),
    ]
    for name, arguments in bad_requests:
        payload = json.loads(part.run_tool_safely(name, arguments))
        assert payload["ok"] is False
        assert payload["error"]


def test_part_six_enforces_file_boundaries_and_approval() -> None:
    part = load_solution("06-permissions-and-limits")

    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        state = part.RunState()

        assert_raises(ValueError, part.resolve_safe_path, "../outside.txt", root)
        assert_raises(ValueError, part.resolve_safe_path, str(root / "absolute.txt"), root)
        assert_raises(ValueError, part.read_text_file, "program.exe", root)

        denied = json.loads(
            part.run_tool_safely(
                "write_text_file",
                '{"path": "denied.md", "content": "no"}',
                root,
                lambda _path, _content: False,
                state,
            )
        )
        assert denied["ok"] is False
        assert not (root / "denied.md").exists()

        oversized_write = json.loads(
            part.run_tool_safely(
                "write_text_file",
                json.dumps(
                    {
                        "path": "oversized.md",
                        "content": "x" * (part.MAX_WRITE_CHARACTERS + 1),
                    }
                ),
                root,
                lambda _path, _content: True,
                state,
            )
        )
        assert oversized_write["ok"] is False
        assert not (root / "oversized.md").exists()

        for index in range(part.MAX_WRITES_PER_RUN):
            payload = json.loads(
                part.run_tool_safely(
                    "write_text_file",
                    json.dumps({"path": f"note-{index}.md", "content": "hello"}),
                    root,
                    lambda _path, _content: True,
                    state,
                )
            )
            assert payload["ok"] is True

        assert part.read_text_file("note-0.md", root) == "hello"

        over_limit = json.loads(
            part.run_tool_safely(
                "write_text_file",
                '{"path": "one-too-many.md", "content": "stop"}',
                root,
                lambda _path, _content: True,
                state,
            )
        )
        assert over_limit["ok"] is False
        assert not (root / "one-too-many.md").exists()

        too_large = root / "large.md"
        too_large.write_bytes(b"x" * (part.MAX_FILE_BYTES + 1))
        assert_raises(ValueError, part.read_text_file, "large.md", root)

        outside = root.parent / f"{root.name}-outside.md"
        outside.write_text("outside", encoding="utf-8")
        link = root / "outside-link.md"
        try:
            try:
                os.symlink(outside, link)
            except (NotImplementedError, OSError):
                # Some Windows setups do not grant permission to create symlinks.
                pass
            else:
                assert "outside-link.md" not in part.list_files(".", root)
                assert_raises(ValueError, part.read_text_file, "outside-link.md", root)
        finally:
            if link.is_symlink():
                link.unlink()
            outside.unlink(missing_ok=True)


def test_part_six_stops_an_oversized_tool_batch() -> None:
    part = load_solution("06-permissions-and-limits")

    class FakeMessage:
        content = None
        tool_calls = [object()] * (part.MAX_TOOL_CALLS_PER_TURN + 1)

        def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
            return {"role": "assistant", "tool_calls": []}

    response = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=FakeMessage())]
    )

    class FakeCompletions:
        def create(self, **_kwargs: Any) -> Any:
            return response

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=FakeCompletions())
    )
    answer = part.run_agent("Try too many tools", client)
    assert "limit" in answer.lower()
    assert str(part.MAX_TOOL_CALLS_PER_TURN) in answer


def test_part_six_stops_at_the_total_tool_budget() -> None:
    part = load_solution("06-permissions-and-limits")

    class FakeMessage:
        content = None

        def __init__(self, turn: int) -> None:
            self.tool_calls = [
                types.SimpleNamespace(
                    id=f"call-{turn}-{index}",
                    function=types.SimpleNamespace(
                        name="get_current_time",
                        arguments="{}",
                    ),
                )
                for index in range(part.MAX_TOOL_CALLS_PER_TURN)
            ]

        def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
            return {"role": "assistant", "tool_calls": []}

    class FakeCompletions:
        def __init__(self) -> None:
            self.turn = 0

        def create(self, **_kwargs: Any) -> Any:
            self.turn += 1
            message = FakeMessage(self.turn)
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=message)]
            )

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=FakeCompletions())
    )
    answer = part.run_agent("Keep requesting the time", client)
    assert "total limit" in answer.lower()
    assert str(part.MAX_TOTAL_TOOL_CALLS) in answer


def test_dashboard_has_six_parts_and_interactions() -> None:
    html = (ROOT / "course" / "index.html").read_text(encoding="utf-8")
    js = (ROOT / "course" / "app.js").read_text(encoding="utf-8")
    combined = html + js
    for part in PARTS:
        assert part in combined
    assert "localStorage" in js
    assert "clipboard" in js.lower()
    assert html.count('class="quiz-card"') == 6
    assert "readonly" in html
