import subprocess
from typing import List, Optional


def run_shell(
    command: str,
    printf: bool = True,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    encoding: str = "utf-8",
) -> str:
    """执行 shell 命令。

    Args:
        command: 要执行的 shell 命令字符串。
        printf: 为 True 时实时输出到终端并返回退出码；
                为 False 时捕获输出并以字符串返回。
        cwd: 命令执行的工作目录，默认为当前目录。
        timeout: 超时时间（秒），None 表示不限时。
        encoding: 捕获输出时使用的编码，默认 utf-8。

    Returns:
        printf=True 时返回退出码字符串，printf=False 时返回 stdout 内容。
    """
    if printf:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                timeout=timeout,
            )
            return str(result.returncode)
        except subprocess.TimeoutExpired:
            return "run shell error: command timed out"
        except Exception as e:
            return f"run shell error: {e}"
    else:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                cwd=cwd,
                timeout=timeout,
                encoding=encoding,
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "run shell error: command timed out"
        except Exception as e:
            return f"run shell error: {e}"


def run_shell_list(
    command_list: List[str],
    printf: bool = True,
    *,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    encoding: str = "utf-8",
) -> str:
    """批量执行 shell 命令，命令之间用 && 连接（前一条失败则终止）。

    Args:
        command_list: 要依次执行的 shell 命令列表。
        printf: 为 True 时实时输出到终端，为 False 时捕获输出。
        cwd: 命令执行的工作目录。
        timeout: 整条命令链的超时时间（秒）。
        encoding: 捕获输出时使用的编码。

    Returns:
        printf=True 时返回退出码字符串，printf=False 时返回 stdout 内容。
    """
    command = " && ".join(command_list)
    return run_shell(
        command, printf=printf, cwd=cwd, timeout=timeout, encoding=encoding
    )
