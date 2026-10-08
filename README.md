# funshell

轻量级 Python shell 命令执行工具：支持实时流式输出或捕获输出为字符串，并提供按端口/
进程名查询与终止进程的 CLI 和 Python API。

## 环境要求

- Python >= 3.10
- 进程/端口查询功能依赖系统命令 `lsof`（优先）或 `ss`（回退），以及 `ps`、`kill`；
  这些命令在主流 Linux 发行版上通常已预装，缺失时可通过系统包管理器安装
  （如 `apt install lsof iproute2 procps`）。

## 安装

```bash
uv add funshell
# 或
pip install funshell
```

## 开发

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## 快速开始

```python
from funshell import run_shell, run_shell_list

# 实时输出到终端，返回退出码（字符串形式）
exit_code = run_shell("echo hello world")
# hello world
# exit_code == "0"

# 捕获输出为字符串
output = run_shell("echo hello world", printf=False)
# output == "hello world"
```

## API

### `run_shell(command, printf=True, *, cwd=None, timeout=None, encoding="utf-8")`

执行一条 shell 命令。

| 参数        | 类型              | 默认值      | 说明                                 |
|-------------|-------------------|-------------|--------------------------------------|
| `command`   | `str`             | 必填        | 要执行的 shell 命令                  |
| `printf`    | `bool`            | `True`      | `True`：实时输出到终端；`False`：捕获输出 |
| `cwd`       | `str \| None`     | `None`      | 命令执行的工作目录                    |
| `timeout`   | `float \| None`   | `None`      | 超时时间（秒）                        |
| `encoding`  | `str`             | `"utf-8"`   | 捕获输出时使用的编码                  |

**返回值：** `printf=True` 时返回退出码字符串；`printf=False` 时返回 stdout 内容字符串。

### `run_shell_list(command_list, printf=True, *, cwd=None, timeout=None, encoding="utf-8")`

依次执行多条命令（用 `&&` 连接，前一条失败则终止后续执行）。

| 参数            | 类型              | 默认值      | 说明                         |
|-----------------|-------------------|-------------|------------------------------|
| `command_list`  | `list[str]`       | 必填        | 要依次执行的命令列表          |
| `printf`        | `bool`            | `True`      | `True`：实时输出；`False`：捕获 |
| `cwd`           | `str \| None`     | `None`      | 工作目录                      |
| `timeout`       | `float \| None`   | `None`      | 整条命令链的超时时间（秒）     |
| `encoding`      | `str`             | `"utf-8"`   | 捕获输出时使用的编码           |

## 示例

```python
from funshell import run_shell, run_shell_list

# 捕获命令输出
result = run_shell("ls -la", printf=False)
print(result)

# 在指定目录下执行
run_shell("git status", cwd="/path/to/repo")

# 设置超时（秒）
run_shell("sleep 100", timeout=5)
# 返回："run shell error: command timed out"

# 依次执行多条命令
run_shell_list(["mkdir -p build", "cd build", "cmake .."])

# 捕获多条命令的输出
output = run_shell_list(["echo hello", "echo world"], printf=False)
# output == "hello\nworld"
```

## 端口/进程查询与终止

按端口号查询占用进程（或按进程名关键字匹配），并可选择直接终止，支持 CLI 和
Python API 两种方式。

### CLI

```bash
# 查询占用 8080 端口的进程
funshell port 8080

# 查询并杀掉
funshell port 8080 --kill

# 按进程名（含任一关键字）查询
funshell name node code-server

# 按进程名查询并用指定信号杀掉
funshell name node --kill --sig TERM
```

### Python API

```python
from funshell import kill_process
from funshell.kill import ProcessFinder

# 一步到位：按端口和/或进程名匹配并杀掉
kill_process(port=8080)
kill_process(name=("code-server",))
kill_process(port=3000, name=("node",), sig="TERM")

# 或先查询再决定是否终止
finder = ProcessFinder().find_by_port(8080)
for proc in finder:
    print(proc)  # pid=42 name=python port=8080 | python3 -m myserver
finder.kill(sig="TERM")
```

`find_by_port` 优先尝试 `lsof`，不可用时回退到 `ss`。若两个命令都不可用，会提示安装
`lsof` 或 `iproute2`。若未查到进程，端口可能被其他用户持有的进程占用（可尝试 `sudo`），
或该进程运行在容器内部。

**注意**：`find_by_name` 按完整命令行（含参数）做子串匹配，匹配范围包含正在执行
`funshell` 本身的进程（例如用 shell 调用 `funshell name foo --kill` 时，命令行里的
`foo` 关键字会让该 `funshell` 进程及其父 shell 一并被匹配到）。请使用足够精确、不会
出现在自身命令行中的关键字，终止前建议先不带 `--kill` 查看一遍匹配结果。

## License

[MIT](LICENSE)

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
