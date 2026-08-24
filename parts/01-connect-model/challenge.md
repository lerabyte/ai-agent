# Part 1 Challenge: Send Your Own Messages

Use your completed `starter/agent.py` for this challenge.

## Task

Replace the greeting and run the program with each of these user messages:

1. `Explain what a Python function is in one sentence.`
2. `What is the current battery percentage on this computer?`
3. `What files are inside the folder containing this program?`

After each run, read the returned message and decide whether it contains a normal answer or would require information from your computer.

## Success check

Run the file and confirm that:

- Python sends each message without an error.
- The general Python question receives a useful answer.
- The battery and file questions do not receive verified computer information.

The connection works in all three cases. The difference is the information available to the model. Part 2 begins with the current-time question and connects it to information Python can read.
