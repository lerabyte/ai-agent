# Part 6 Challenge: Add a Safe Append Tool

Add `append_text_file(path, content)`, which appends text to an existing allowed file.

It must:

1. resolve the path inside `WORKSPACE_ROOT`;
2. reject symlinks and unsupported extensions;
3. read the existing file size before changing anything;
4. reject the action if the **final UTF-8 file size** would exceed `MAX_FILE_BYTES`;
5. show the destination, appended text length, and a clearly labeled truncated preview;
6. ask for human approval;
7. share `RunState`, so a successful append counts toward `MAX_WRITES_PER_RUN`;
8. return a structured error on denial or failure;
9. never call a shell command.

Calculate the final size before approval:

```python
final_size = current_size + len(content.encode("utf-8"))
```

Do not partially append when the limit would be exceeded.

## Security checks

Confirm that these fail safely:

```python
resolve_safe_path("../../outside.txt")
resolve_safe_path("/tmp/outside.txt")
read_text_file("program.exe")
```

Also create a symlink inside the workspace during a test and confirm that `list_files` omits it.
