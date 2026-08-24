# Part 1: Connect a Local Model to Python

## Goal

Connect Python to `gpt-oss:20b` running in Ollama, send a simple greeting, and print the model's answer.

By the end of this part, the data will move like this:

1. Python creates a message.
2. The OpenAI client sends it to Ollama at `localhost`.
3. Ollama runs the local model.
4. Python receives and prints the response.

## Before you start

You need:

- Python 3.10 or newer
- [Ollama](https://ollama.com/download)
- The OpenAI Python package
- Enough memory to run `gpt-oss:20b` locally

Install the Python package:

```bash
python -m pip install openai
```

Download the model:

```bash
ollama pull gpt-oss:20b
```

Make sure Ollama is open and running before you start the Python file.

## Start with the starter file

Open [`starter/agent.py`](starter/agent.py). It already contains the model name, local address, API-key placeholder, and the greeting.

Complete the two `TODO` sections:

1. Call `client.chat.completions.create(...)` with the model and messages.
2. Print `response.choices[0].message.content`.

Run it from the repository root:

```bash
python parts/01-connect-model/starter/agent.py
```

You can compare your work with [`solution/agent.py`](solution/agent.py).

## Read the important lines

```python
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)
```

`localhost` means the request stays on this computer. Port `11434` is the local address Ollama uses for its API. The client requires an API-key field, but Ollama does not authenticate this local request, so `ollama` is only a placeholder.

```python
messages = [
    {"role": "user", "content": "Hello! This is Lera."},
]
```

A model receives a list of messages. Each message has a `role` and `content`. Here, the role says the message came from the user, and the content is the text sent to the model.

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
)
```

This line sends the request and waits for the local model. The returned object contains the model's response. The first response message is stored at `response.choices[0].message`.

## Check your result

The terminal should show a reply to the greeting. That confirms the entire connection: Python created the message, Ollama passed it to the local model, and Python received the returned text.

If Python reports a connection error, check that Ollama is running. If it reports that the model is missing, run the `ollama pull` command again and confirm that `MODEL` is exactly `gpt-oss:20b`.

## Practice

Complete [`challenge.md`](challenge.md), then continue to Part 2. There, a question about the computer's current time will reveal the next connection we need to build.

The local connection follows the [official OpenAI guide for running gpt-oss with Ollama](https://developers.openai.com/cookbook/articles/gpt-oss/run-locally-ollama).
