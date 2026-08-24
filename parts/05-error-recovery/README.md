# Part 5: Recovering From Tool Errors

Part 4 can dispatch several tools, but malformed JSON, missing arguments, bad types, an unknown tool, or division by zero can still crash the starter. This part turns each failure into a result the model can read:

```json
{"ok": false, "error": "Cannot divide by zero."}
```

Python attaches that result to the original `tool_call_id`. The model can then correct its request or explain the problem, and the loop remains in control.

## Build it

Open [`starter/agent.py`](starter/agent.py), then update `run_tool_safely`:

1. Parse the argument JSON inside `try`/`except`.
2. Reject tool names outside `TOOL_DISPATCH`.
3. Require a JSON object with exactly the expected keys.
4. Validate every value before calling the function.
5. Return `{"ok": true, "result": ...}` on success.
6. Return `{"ok": false, "error": ...}` for a recoverable failure.

Compare with [`solution/agent.py`](solution/agent.py).

## The calculator's validation rules

- `a` and `b` may be JSON integers such as `5` or JSON decimals such as `5.5`.
- `true` and `false` are rejected. Python normally treats `bool` as a kind of `int`, so the code checks for Boolean values first.
- `operation` must be a JSON string.
- The calculator itself allows only `add`, `subtract`, `multiply`, or `divide`.
- Dividing by zero returns an error result instead of crashing.

The tool schema helps the model format a call, but Python still enforces all of these rules.

## The stopping condition

`MAX_STEPS` limits how many times Python asks the model what to do next. If no final answer arrives within that many model turns, Python stops with its own message.

## Run it

```bash
python parts/05-error-recovery/solution/agent.py
```

Use this prompt:

```text
Use the calculate tool to divide 20 by 0. If it fails, explain the error without guessing a result.
```

## What to remember

- Validate model-generated data even when the schema is correct.
- Tool failures should return to the model as data, not crash Python.
- Reject Boolean values explicitly when a JSON number is required.
- Every agent loop needs a stopping condition.

Primary reference: [How to run gpt-oss locally with Ollama](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama), especially its Chat Completions tool-calling flow. The [official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling) provides the general tool-result pattern.

Next: [Part 6: Permissions and Limits](../06-permissions-and-limits/README.md).
