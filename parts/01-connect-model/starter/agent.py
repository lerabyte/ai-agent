"""Part 1 starter: connect the local model to Python."""

from openai import OpenAI


MODEL = "gpt-oss:20b"


def main() -> None:
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )

    messages = [
        {"role": "user", "content": "Hello! This is Lera."},
    ]

    # TODO 1: Send `messages` to `MODEL` with
    # client.chat.completions.create(...).

    # TODO 2: Print the text in the first returned message.
    print("Complete the two TODOs, then run this file again.")


if __name__ == "__main__":
    main()
