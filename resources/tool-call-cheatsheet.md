# Tool-Call Cheat Sheet

## The complete exchange

```text
1. User message
2. Model tool request
3. Python runs the matching function
4. Python appends the tool result
5. Model reads the result
6. Model requests another tool or returns a final answer
```

## The two things a tool needs

1. A Python function that performs the action.
2. A JSON schema that describes the action to the model.

## The messages that must be preserved

```text
user       original request
assistant  complete model message, including its tool call
tool       result connected with tool_call_id
assistant  next decision or final answer
```

## The core stopping condition

```python
if not assistant_message.tool_calls:
    return assistant_message.content
```

## Safe defaults

- Dispatch only tool names registered in Python.
- Validate every argument before using it.
- Return tool errors to the model as data.
- Restrict file paths to one workspace.
- Ask before write actions.
- Stop after a fixed number of steps.
- Never give the model arbitrary shell access in a beginner project.

