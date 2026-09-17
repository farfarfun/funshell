#!/usr/bin/env python3
"""
funshell 命令行入口：查询端口/进程名占用情况，可选直接杀掉。

示例:

    funshell port 8080            # 查询占用 8080 端口的进程
    funshell port 8080 --kill     # 查询并杀掉
    funshell name node code       # 按进程名（含任一关键字）查询
    funshell name node --kill --sig TERM
"""

from typing import List

import typer

from .kill import ProcessFinder

app = typer.Typer(help="查询端口/进程名占用情况，可选直接杀掉。")


def _print_procs(finder: ProcessFinder) -> None:
    if not finder:
        typer.echo("no matching process found")
        return
    for proc in finder:
        typer.echo(str(proc))


@app.command()
def port(
    port: int = typer.Argument(..., help="端口号"),
    kill: bool = typer.Option(False, "--kill", help="查询后直接杀掉"),
    sig: str = typer.Option("9", "--sig", help="kill 信号，默认 9 (KILL)"),
) -> None:
    """按端口号查询占用进程"""
    finder = ProcessFinder().find_by_port(port)
    _print_procs(finder)
    if kill and finder:
        finder.kill(sig=sig)


@app.command()
def name(
    pattern: List[str] = typer.Argument(..., help="进程名关键字，可传多个"),
    kill: bool = typer.Option(False, "--kill", help="查询后直接杀掉"),
    sig: str = typer.Option("9", "--sig", help="kill 信号，默认 9 (KILL)"),
) -> None:
    """按进程名（关键字）查询进程"""
    finder = ProcessFinder().find_by_name(tuple(pattern))
    _print_procs(finder)
    if kill and finder:
        finder.kill(sig=sig)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
