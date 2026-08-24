# Part 4 Challenge: Add a Character Counter

Add a fourth tool named `count_characters`.

It should:

1. accept one string argument named `text`;
2. count spaces and punctuation as characters;
3. appear in both `TOOLS` and `TOOL_DISPATCH`;
4. work through the existing `run_agent` loop.

Test it with:

```text
Count the words and characters in "Tools turn decisions into actions".
```

## Stretch goal

Add a separate `count_lines(text)` tool. Do not add special cases for either new tool inside `run_agent`; dispatch should remain the one place that connects names to functions.
