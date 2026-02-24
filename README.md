# funshell

A lightweight Python utility for executing shell commands, supporting real-time output streaming and captured output.

## Installation

```bash
pip install funshell
```

## Quick Start

```python
from run import run_shell, run_shell_list

# Real-time output to terminal, returns exit code
exit_code = run_shell("echo hello world")
# hello world
# exit_code == "0"

# Capture output as string
output = run_shell("echo hello world", printf=False)
# output == "hello world"
```

## API

### `run_shell(command, printf=True, *, cwd=None, timeout=None, encoding="utf-8")`

Execute a shell command.

| Parameter  | Type           | Default   | Description                                          |
|------------|----------------|-----------|------------------------------------------------------|
| `command`  | `str`          | required  | Shell command to execute                             |
| `printf`   | `bool`         | `True`    | `True`: stream to terminal; `False`: capture output  |
| `cwd`      | `str \| None`  | `None`    | Working directory for the command                    |
| `timeout`  | `float \| None`| `None`    | Timeout in seconds                                   |
| `encoding` | `str`          | `"utf-8"` | Output encoding when capturing                       |

**Returns:** Exit code as string when `printf=True`, stdout content when `printf=False`.

### `run_shell_list(command_list, printf=True, *, cwd=None, timeout=None, encoding="utf-8")`

Execute multiple commands sequentially (joined with `&&`, stops on first failure).

| Parameter      | Type           | Default   | Description                              |
|----------------|----------------|-----------|------------------------------------------|
| `command_list` | `list[str]`    | required  | List of shell commands                   |
| `printf`       | `bool`         | `True`    | `True`: stream; `False`: capture         |
| `cwd`          | `str \| None`  | `None`    | Working directory                        |
| `timeout`      | `float \| None`| `None`    | Timeout for the entire command chain     |
| `encoding`     | `str`          | `"utf-8"` | Output encoding                          |

## Examples

```python
from run import run_shell, run_shell_list

# Capture command output
result = run_shell("ls -la", printf=False)
print(result)

# Run in a specific directory
run_shell("git status", cwd="/path/to/repo")

# Set a timeout (seconds)
run_shell("sleep 100", timeout=5)
# Returns: "run shell error: command timed out"

# Execute a sequence of commands
run_shell_list(["mkdir -p build", "cd build", "cmake .."])

# Capture output of chained commands
output = run_shell_list(["echo hello", "echo world"], printf=False)
# output == "hello\nworld"
```

## License

[MIT](LICENSE)
