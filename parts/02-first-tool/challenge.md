# Part 2 Challenge: Add a Tool Argument

Change `get_current_time` so the model can choose between 12-hour and 24-hour time.

## Task

1. Add a `time_format` parameter to the Python function.
2. Add `time_format` to the tool's JSON schema.
3. Allow only `12_hour` and `24_hour`.
4. Mark `time_format` as required.
5. Read the requested value from `tool_call.function.arguments`.
6. Pass that value into the Python function.

Suggested schema for the new property:

```python
"time_format": {
    "type": "string",
    "enum": ["12_hour", "24_hour"],
    "description": "Choose how the returned time should be formatted.",
}
```

Use `%I:%M:%S %p` for 12-hour time and `%H:%M:%S` for 24-hour time.

## Success check

Ask the model for the current time in 24-hour format. Confirm that:

- The tool call contains `"time_format": "24_hour"`.
- Python passes that argument into the function.
- The final answer contains a 24-hour time.

Then change the question to request 12-hour time and run it again.
