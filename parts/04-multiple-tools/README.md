# Part 4: Letting the Agent Choose Between Tools

Part 3 gave us a repeating tool loop. Before adding more tools, we move that loop out of `main()` and into:

```python
run_agent(user_message, client)
```

`run_agent` creates the message history, runs the same `while True` loop from Part 3, and returns when the model gives final text. `main()` now only creates the client, reads the user's prompt, calls `run_agent`, and prints the answer. This keeps the loop in one reusable function while we expand it.

This part gives that loop three choices:

- `get_current_time()` reads the computer's clock.
- `calculate(a, b, operation)` adds, subtracts, multiplies, or divides two numbers.
- `count_words(text)` counts words.

## Dispatch

The model returns a tool name and JSON arguments. Python looks up that name in one explicit dictionary:

```text
model requests "calculate"
            ↓
Python finds calculate in TOOL_DISPATCH
            ↓
calculate(a, b, operation) runs
            ↓
the result returns to the model
```

The calculator itself stays simple and visible. An `if`/`elif` block permits exactly `add`, `subtract`, `multiply`, and `divide`, and it rejects division by zero. There is no general expression runner.

## Build it

Open [`starter/agent.py`](starter/agent.py). The three Python functions and the reusable loop are already present, but only the time tool is connected.

1. Describe `calculate` in `TOOLS` with required arguments `a`, `b`, and `operation`.
2. Describe `count_words` in `TOOLS` with required argument `text`.
3. Connect both names to their functions in `TOOL_DISPATCH`.
4. Compare your result with [`solution/agent.py`](solution/agent.py).

The `operation` schema should allow only:

```text
add, subtract, multiply, divide
```

## Run it

```bash
python parts/04-multiple-tools/solution/agent.py
```

Try:

```text
Tell me the current time, multiply 18 by 7, and count the words in "Agents connect models to useful actions."
```

The model may request several tools in one response or across several turns. The loop handles both.

## What to remember

- `run_agent` contains the reusable loop from Part 3.
- Tool schemas describe the choices to the model.
- `TOOL_DISPATCH` is Python's allowlist of functions that may actually run.
- The model requests an action; Python performs it.

Primary reference: [How to run gpt-oss locally with Ollama](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama), including its OpenAI-compatible local client and tool-calling examples. For the general five-step pattern, see the [official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

Next: [Part 5: Error Recovery](../05-error-recovery/README.md).
