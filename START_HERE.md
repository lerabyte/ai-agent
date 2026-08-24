# Start Here

Use the course in this order:

1. Open `course/index.html` in a browser. It stores your progress on your computer.
2. Read the lesson for Part 1.
3. Open that part's `starter/agent.py` and complete its TODOs.
4. Run your code from the repository root.
5. Compare it with `solution/agent.py`.
6. Complete `challenge.md`.
7. Mark the part complete on the dashboard and continue.

## Before Part 1

```bash
ollama pull gpt-oss:20b
python -m venv .venv
```

Activate the environment:

```bash
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then install the course package and make sure Ollama is running:

```bash
python -m pip install -r requirements.txt
```

All commands in the lessons are written to run from this repository's root folder.

## What changes in each part

```text
Part 1  Python can send and receive text.
Part 2  The model can request one action.
Part 3  The model can continue after each action.
Part 4  The model can choose between several actions.
Part 5  Tool errors become information the model can use.
Part 6  Python enforces permissions, paths, approvals, and limits.
```

The examples stay small so each new piece is visible in the code.
