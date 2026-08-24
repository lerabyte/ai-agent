# Part 6: Permissions and Limits

The final agent adds controlled file actions while keeping the time, calculator, and word-counter tools.

| Tool | Permission |
| --- | --- |
| `list_files` | List allowed, non-hidden, non-symlink items in the workspace |
| `read_text_file` | Read a small allowed UTF-8 text file |
| `write_text_file` | Create or replace an allowed text file after human approval |

## The file boundary

The solution creates `agent_workspace` beside `agent.py`. Python resolves every requested path and proves it remains inside that folder. It rejects absolute paths, paths that escape with `..`, unsupported extensions, oversized files, and non-text data. `list_files` skips symbolic links.

There is no shell, delete, network, or arbitrary-code tool.

## Four independent limits

- `MAX_STEPS` limits model turns.
- `MAX_TOOL_CALLS_PER_TURN` rejects a response containing too many tool requests.
- `MAX_TOTAL_TOOL_CALLS` stops the entire run before its cumulative tool-call budget is exceeded.
- `MAX_WRITES_PER_RUN` rejects writes after the successful-write budget is reached.

These checks run in Python, so the model cannot remove them in a message.

## Write approval

Before a write, Python shows:

- whether the action creates or overwrites a file;
- the exact destination;
- the total proposed character length;
- either the full content or a clearly labeled truncated preview.

Only `y` or `yes` approves the write. A denial returns to the model as a structured error.

## Build it

Open [`starter/agent.py`](starter/agent.py):

1. Implement `resolve_safe_path`.
2. Implement `list_files`, skipping hidden items and symlinks and stopping at `MAX_LISTED_ITEMS`.
3. Implement size-limited `read_text_file`.
4. Implement approval-gated `write_text_file` and update `RunState` after success.
5. Add the three file schemas, validation rules, and dispatch entries.
6. Enforce all four limits before performing tool calls or writes.

Compare with [`solution/agent.py`](solution/agent.py).

## Run it

```bash
python parts/06-permissions-and-limits/solution/agent.py
```

Try:

```text
Create study-plan.md with three short tasks, then read it and summarize it.
```

Then verify the sandbox:

```text
Read ../../outside.txt
```

## What to remember

- Give an agent the smallest useful tool set.
- Enforce permissions and budgets in Python, not only in prompts.
- Ask before changing data.
- Treat every model-generated path and argument as untrusted input.

Primary reference: [How to run gpt-oss locally with Ollama](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama), including its local OpenAI client and tool-calling examples. The [official function-calling guide](https://developers.openai.com/api/docs/guides/function-calling) describes the general conversation pattern.
