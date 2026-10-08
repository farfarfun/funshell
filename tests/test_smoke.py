"""funshell 公共 API 的轻量测试。

测试使用无害命令，并 mock 进程发现与终止操作，避免依赖主机进程表或真的终止进程。
"""

import subprocess
from unittest.mock import patch

import pytest


def test_import_top_level():
    import funshell

    assert hasattr(funshell, "run_shell")
    assert hasattr(funshell, "run_shell_list")
    assert hasattr(funshell, "kill_process")
    assert funshell.__all__ == ["run_shell", "run_shell_list", "kill_process"]


def test_import_submodules():
    from funshell import kill, run

    assert run is not None
    assert kill is not None


def test_run_shell_printf_true_returns_exit_code_string():
    from funshell import run_shell

    result = run_shell("echo hello", printf=True)
    assert result == "0"


def test_run_shell_printf_false_captures_output():
    from funshell import run_shell

    result = run_shell("echo hello world", printf=False)
    assert result == "hello world"


def test_run_shell_nonzero_exit_code():
    from funshell import run_shell

    result = run_shell("exit 3", printf=True)
    assert result == "3"


def test_run_shell_timeout_is_handled():
    from funshell import run_shell

    result = run_shell("sleep 5", printf=True, timeout=0.1)
    assert result == "run shell error: command timed out"


def test_run_shell_list_joins_commands_with_and():
    from funshell import run_shell_list

    result = run_shell_list(["echo a", "echo b"], printf=False)
    assert result == "a\nb"


def test_run_shell_list_printf_true_returns_exit_code():
    from funshell import run_shell_list

    result = run_shell_list(["echo a", "echo b"], printf=True)
    assert result == "0"


def test_proc_info_str():
    from funshell.kill import ProcInfo

    info = ProcInfo(pid=123, name="python", cmd="python3 -m foo", port=8080)
    text = str(info)
    assert "pid=123" in text
    assert "port=8080" in text


def test_process_finder_find_by_name_no_patterns_is_noop():
    from funshell.kill import ProcessFinder

    finder = ProcessFinder()
    result = finder.find_by_name(None)
    assert result is finder
    assert len(finder) == 0


def test_process_finder_find_by_name_mocked():
    from funshell.kill import ProcessFinder

    fake_ps_output = (
        "  PID COMMAND         COMMAND\n"
        "  123 python          python3 /usr/bin/foo --serve\n"
        "  456 bash            /bin/bash\n"
    )
    completed = subprocess.CompletedProcess(
        args=["ps"], returncode=0, stdout=fake_ps_output, stderr=""
    )
    with patch("funshell.kill.subprocess.run", return_value=completed) as mock_run:
        finder = ProcessFinder()
        result = finder.find_by_name(("foo",))

    mock_run.assert_called_once()
    assert result is finder
    assert len(finder) == 1
    assert finder.procs[0].pid == 123
    assert list(iter(finder))[0].pid == 123


def test_process_finder_find_by_port_mocked_lsof():
    from funshell.kill import ProcessFinder

    fake_lsof_output = (
        "COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME\n"
        "python  42   user   3u  IPv4 12345      0t0  TCP *:8080 (LISTEN)\n"
    )
    completed = subprocess.CompletedProcess(
        args=["lsof"], returncode=0, stdout=fake_lsof_output, stderr=""
    )
    with patch("funshell.kill.subprocess.run", return_value=completed):
        finder = ProcessFinder()
        result = finder.find_by_port(8080)

    assert result is finder
    assert len(finder) == 1
    assert finder.procs[0].pid == 42
    assert finder.procs[0].port == 8080


def test_process_finder_find_by_port_falls_back_when_lsof_is_missing():
    from funshell.kill import ProcessFinder

    ss_output = (
        "State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process\n"
        'LISTEN 0      128    *:8080            *:*             users:(("python",pid=42,fd=3))\n'
    )
    completed = subprocess.CompletedProcess(
        args=["ss"], returncode=0, stdout=ss_output, stderr=""
    )
    with (
        patch(
            "funshell.kill.subprocess.run", side_effect=[FileNotFoundError(), completed]
        ),
        patch.object(ProcessFinder, "_get_proc_name", return_value="python"),
    ):
        finder = ProcessFinder().find_by_port(8080)

    assert [proc.pid for proc in finder] == [42]


def test_process_finder_find_by_port_reports_when_lsof_and_ss_are_missing():
    from funshell.kill import PortQueryCommandNotFoundError, ProcessFinder

    with patch("funshell.kill.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(PortQueryCommandNotFoundError, match="lsof.*ss"):
            ProcessFinder().find_by_port(8080)


def test_process_finder_kill_never_runs_real_kill_command():
    from funshell.kill import ProcessFinder

    finder = ProcessFinder()
    with patch("funshell.kill._run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["kill"], returncode=0, stdout="", stderr=""
        )
        outcomes = finder.kill(pids=[999999])

    mock_run.assert_called_once_with(["kill", "-9", "999999"])
    assert outcomes == [(999999, True)]


def test_kill_process_with_no_args_is_noop_and_touches_nothing():
    from funshell.kill import kill_process

    # 不传端口和进程名时不应执行任何子进程调用。
    assert kill_process() == []


def test_kill_process_mocked_end_to_end():
    from funshell.kill import kill_process

    fake_ps_output = (
        "  PID COMMAND         COMMAND\n  789 myproc          myproc --run\n"
    )
    completed = subprocess.CompletedProcess(
        args=["ps"], returncode=0, stdout=fake_ps_output, stderr=""
    )
    with (
        patch("funshell.kill.subprocess.run", return_value=completed) as mock_run,
    ):
        outcomes = kill_process(name=("myproc",))

    assert mock_run.call_args_list[-1].args[0] == ["kill", "-9", "789"]
    assert outcomes == [(789, True)]


def test_process_finder_kill_reports_failure_and_signal():
    """底层 kill 失败时返回 False，并保留指定信号。"""
    from funshell.kill import ProcessFinder

    failed = subprocess.CompletedProcess(
        args=["kill"], returncode=1, stdout="", stderr="denied"
    )
    with patch("funshell.kill._run", return_value=failed) as run:
        outcomes = ProcessFinder().kill(pids=[123], sig="TERM")

    run.assert_called_once_with(["kill", "-15", "123"])
    assert outcomes == [(123, False)]
