# Part 3: Build the Agent Loop

## Goal

Keep calling the model and running its requested tools until it returns a final text answer.

Part 2 used two fixed model requests:

1. Request a tool.
2. Return its result and request the final answer.

That works for one tool round. An agent needs to continue when the model requests another action, so this part moves the same sequence into a loop.

## Start with the starter file

[`starter/agent.py`](starter/agent.py) contains the complete Part 2 program. It handles one tool request and then stops after the second model response.

Run it once before changing it:

```bash
python parts/03-agent-loop/starter/agent.py
```

## The loop

The solution repeats four steps:

1. Send the complete message history to the model.
2. Add the model's response to the history.
3. If there are no tool calls, print the final answer and stop.
4. Otherwise, run every requested tool, add each result, and return to step 1.

The stopping condition is important:

```python
if not assistant_message.tool_calls:
    print(assistant_message.content)
    break
```

No tool call means the model is ready to answer the user. `break` ends the loop.

## Why the history keeps growing

The model does not remember previous Python requests on its own. Each request receives the `messages` list again, so the list must preserve:

- the user's question
- every assistant tool request
- every tool result

Removing one of these messages breaks the sequence. A tool result must also keep the matching `tool_call_id`.

## Run the solution

```bash
python parts/03-agent-loop/solution/agent.py
```

The terminal should print a final answer containing the time returned by Python. The number of model calls is no longer hard-coded; the loop stops when the model answers without requesting another tool.

Open [`solution/agent.py`](solution/agent.py) and find:

- `while True`, which starts the repeated process
- the `break`, which stops after a final answer
- the `for` loop, which handles every tool call in one response
- `run_tool`, which allows only known Python functions

This first loop runs until the model returns text. If a local model keeps requesting the tool, press `Ctrl+C` to stop it. Part 5 adds a fixed model-turn limit so the program can stop on its own.

## Try another question

Change the user message to:

> Use the clock tool, then explain whether it is morning, afternoon, evening, or night.

The same loop can handle the new request without changing its control flow.

## Practice

Complete [`challenge.md`](challenge.md). In Part 4, the same loop can be connected to more than one tool.

The local API and tool format follow the [official OpenAI Ollama guide](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama).
