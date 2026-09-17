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

## Port / Process Lookup & Kill

Query which process is holding a port (or match by process name), and optionally kill it — via CLI or Python API.

### CLI

```bash
# Query which process is listening on port 8080
funshell port 8080

# Query and kill it
funshell port 8080 --kill

# Match by process name (any of the given keywords)
funshell name node code-server

# Match by name and kill with a specific signal
funshell name node --kill --sig TERM
```

### Python API

```python
from funshell import kill_process
from funshell.kill import ProcessFinder

# One-shot: kill whatever matches port and/or name
kill_process(port=8080)
kill_process(name=("code-server",))
kill_process(port=3000, name=("node",), sig="TERM")

# Or inspect before killing
finder = ProcessFinder().find_by_port(8080)
for proc in finder:
    print(proc)  # pid=42 name=python port=8080 | python3 -m myserver
finder.kill(sig="TERM")
```

`find_by_port` tries `lsof` first, falling back to `ss` if unavailable. If no process is found, the port may be held by another user (try `sudo`) or a process inside a container.

## License

[MIT](LICENSE)
