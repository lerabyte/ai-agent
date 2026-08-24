# Part 3 Challenge: Ask Questions at Runtime

Turn the fixed example into a small command-line program.

## Task

Replace the hard-coded user message with text collected from:

```python
question = input("Ask the agent: ").strip()
```

If the user presses Enter without typing a question, print a short message and end the program without calling the model.

If a question is present, place it in the first user message and run the same agent loop.

## Success check

Run the file three times:

1. Ask for the computer's current time. The agent should use the tool.
2. Ask a general question that does not need the clock. The agent should answer without a tool call.
3. Press Enter without typing. The program should end cleanly.

The loop itself should not contain the original hard-coded question.
