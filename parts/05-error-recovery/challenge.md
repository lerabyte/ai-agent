# Part 5 Challenge: Recover From Bad Arguments

Add `repeat_text(text, times)`. `times` must be a JSON integer from 1 through 5.

Reject:

- missing or extra arguments;
- `times` supplied as a string or decimal;
- `times` supplied as `true` or `false`;
- values below 1 or above 5.

Every rejection must return:

```json
{"ok": false, "error": "A short explanation"}
```

The agent loop must continue after the error.

## Direct checks

```python
run_tool_safely(
    "calculate",
    '{"a": 5, "b": 0, "operation": "divide"}',
)
```

The returned JSON should contain `"ok": false`. Also check that `{"a": true, "b": 2, "operation": "add"}` is rejected.
