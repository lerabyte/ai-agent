# Part 2: Give the Model Its First Tool

## Goal

Let the model request the computer's current time, run the matching Python function, return its result, and ask the model for a final answer.

Part 1 gave Python two abilities: send text to the model and receive text back. Now change the greeting to a question about this computer:

> What time is it on this computer right now?

Run the starter before completing its TODOs. The model cannot verify the answer from the message alone because the request does not include the computer's clock. Python can read the clock, so this part connects that Python action to the model.

After the first run, the code adds “Use the available tool” so the model reliably demonstrates the tool request during the lesson.

## Start with the starter file

Open [`starter/agent.py`](starter/agent.py) and run it:

```bash
python parts/02-first-tool/starter/agent.py
```

It begins with the Part 1 connection, the time function, and its tool description. Complete the four focused `TODO` sections to:

1. make the tool request predictable and send the tool description to the model;
2. parse the returned JSON arguments;
3. run the Python function;
4. return the result in a second model request.

## Step 1: Read the Python function

```python
def get_current_time() -> str:
    now = datetime.now().astimezone()
    return now.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z")
```

This is a normal Python function. The model never runs it directly.

## Step 2: Read its tool description

The `TOOLS` list tells the model which actions it may request. The description includes:

- `name`: the exact function name
- `description`: when the function is useful
- `parameters`: the input the function accepts

`get_current_time` needs no input, so its object has no properties.

## Step 3: Let the model request the tool

Include `tools=TOOLS` in the first model request. The response may now contain `message.tool_calls` instead of a final text answer.

A tool call contains the requested function name, its arguments, and an ID. It is only a request. Python must decide whether the name is allowed and run the matching function.

The arguments arrive as JSON text. `json.loads(...)` turns that text into a Python dictionary before the function is called.

## Step 4: Return the result

The message history must contain all three events in order:

| Role | What it contains |
|---|---|
| `user` | The original time question |
| `assistant` | The model's tool request |
| `tool` | The time returned by Python |

The tool result includes `tool_call_id`, which connects it to the model's request.

Append the model's complete assistant message to the history. Do not rebuild only its role and tool calls; keeping the complete returned message preserves the information the model may need on the next request.

Send the updated history to the model one more time. It can now use the returned time in its final answer.

## Run the solution

```bash
python parts/02-first-tool/solution/agent.py
```

The terminal should print a response containing the current local time. Compare the time with your computer's clock.

Read [`solution/agent.py`](solution/agent.py) from top to bottom and follow this exact sequence:

1. Ask the model.
2. Read its tool request.
3. Run the allowed Python function.
4. Add the tool result to the history.
5. Ask the model again.
6. Print the final answer.

## Practice

Complete [`challenge.md`](challenge.md), then continue to Part 3 to repeat this process until the model returns a final answer.

This function-calling sequence follows the [official OpenAI Ollama guide](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama).
