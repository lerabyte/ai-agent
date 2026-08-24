"""Part 1 solution: send one message to a local model."""

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

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    answer = response.choices[0].message.content
    print(answer or "The model returned no text.")


if __name__ == "__main__":
    main()
