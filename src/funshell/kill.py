#!/usr/bin/env python3
"""
按进程名或端口查找进程，并可终止。仅作为模块被 Python 代码调用。
不传进程名/端口则不执行对应逻辑。

示例:

    from scripts.find_port import ProcessFinder, kill_process

    tool = ProcessFinder()
    tool.find_by_name(("code-server", "jupyter"))
    tool.find_by_port(8080).kill(sig="KILL")

    kill_process(port=8080)
    kill_process(name=("code-server",))
    kill_process(port=3000, name=("node",))
"""

import re
import subprocess
from dataclasses import dataclass
from nltlog import getLogger

logger = getLogger("funshell")


@dataclass
class ProcInfo:
    pid: int
    name: str
    cmd: str
    port: int | None = None

    def __str__(self):
        port_str = f" port={self.port}" if self.port is not None else ""
        return f"pid={self.pid} name={self.name}{port_str} | {self.cmd[:80]}"


def _run(cmd: list[str], text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=text,
        timeout=10,
    )


class ProcessFinder:
    """按进程名或端口查找进程，并可终止。查找结果保存在 .procs，便于链式调用 kill()。"""

    def __init__(self) -> None:
        self.procs: list[ProcInfo] = []

    def find_by_name(self, patterns: tuple[str, ...] | None = None) -> "ProcessFinder":
        """按进程名（包含任一 pattern）查找。不传 patterns 则不执行。返回 self。"""
        self.procs = []
        if patterns is None:
            return self
        pattern_re = re.compile(
            "|".join(re.escape(p) for p in patterns),
            re.IGNORECASE,
        )
        out = _run(["ps", "-eo", "pid,comm,args"]).stdout
        seen: set[int] = set()
        for line in out.strip().split("\n")[1:]:
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            pid_s, comm, args = parts[0], parts[1], parts[2]
            try:
                pid = int(pid_s)
            except ValueError:
                continue
            if pid in seen:
                continue
            full = f"{comm} {args}"
            if pattern_re.search(full):
                seen.add(pid)
                self.procs.append(ProcInfo(pid=pid, name=comm, cmd=args))
        if self.procs:
            logger.success(
                f"find_by_name patterns={patterns} -> {len(self.procs)} process(es)"
            )
        return self

    def find_by_port(self, port: int) -> "ProcessFinder":
        """按监听端口查找进程（macOS/Linux 用 lsof）。返回 self 便于链式调用。"""
        out = _run(["lsof", "-i", f":{port}", "-P", "-n"]).stdout
        self.procs = []
        seen: set[int] = set()
        for line in out.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[1])
            except ValueError:
                continue
            if pid in seen:
                continue
            seen.add(pid)
            cmd = " ".join(parts[8:]) if len(parts) > 8 else parts[1]
            self.procs.append(ProcInfo(pid=pid, name=parts[0], cmd=cmd, port=port))
        if self.procs:
            logger.success(f"find_by_port port={port} -> {len(self.procs)} process(es)")
        return self

    def kill(
        self,
        *,
        procs: list[ProcInfo] | None = None,
        pids: list[int] | None = None,
        sig: str = "9",
    ) -> list[tuple[int, bool]]:
        """终止进程。不传 procs/pids 时使用本次查找结果 self.procs。返回 (pid, success) 列表。"""
        if pids is not None:
            pid_list = pids
        elif procs is not None:
            pid_list = [p.pid for p in procs]
        else:
            pid_list = [p.pid for p in self.procs]
        outcomes: list[tuple[int, bool]] = []
        for pid in pid_list:
            r = _run(["kill", f"-{sig}", str(pid)])
            ok = r.returncode == 0
            outcomes.append((pid, ok))
            if ok:
                logger.success(f"kill -{sig} {pid}")
            else:
                logger.warning(f"kill -{sig} {pid} failed")
        return outcomes

    def __len__(self) -> int:
        return len(self.procs)

    def __iter__(self):
        return iter(self.procs)


def kill_process(
    port: int | None = None,
    name: str | tuple[str, ...] | None = None,
    *,
    sig: str = "TERM",
) -> list[tuple[int, bool]]:
    """按进程名和/或端口号杀进程。不传则不执行对应项；都未传则返回 []。"""
    finder = ProcessFinder()
    pids: set[int] = set()
    if port is not None:
        finder.find_by_port(port)
        pids.update(p.pid for p in finder.procs)
    if name is not None:
        pats = (name,) if isinstance(name, str) else name
        finder.find_by_name(pats)
        pids.update(p.pid for p in finder.procs)
    if not pids:
        logger.info("kill_process: no processes matched (port=%s, name=%s)", port, name)
        return []
    outcomes = finder.kill(pids=list(pids), sig=sig)
    ok_count = sum(1 for _, ok in outcomes if ok)
    logger.success(
        f"kill_process port={port} name={name} -> killed {ok_count}/{len(outcomes)}"
    )
    return outcomes
