# Security Notes

This repository is an educational agent harness, not a production security boundary.

The final lesson demonstrates several important controls:

- an explicit tool allowlist;
- argument validation;
- a fixed workspace directory;
- approval before file writes;
- a maximum step count;
- errors returned as tool results instead of unhandled crashes.

The course intentionally does not provide a general shell tool. Never connect untrusted model output directly to `eval`, `exec`, `subprocess`, a database, or unrestricted filesystem operations.

Do not place secrets inside prompts, example files, or this repository. The value `ollama` used as an API key is only a dummy field for the local client.

