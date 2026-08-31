"""Lightweight smoke tests for funshell.

Scope: verify the public surface (`funshell.run_shell`, `funshell.run_shell_list`,
`funshell.kill_process`, `funshell.kill.ProcessFinder`) imports and behaves
sensibly, without running destructive commands.

Notes:
- `run_shell`/`run_shell_list` are exercised with harmless, deterministic
  commands (`echo`, `exit N`) since that's exactly the feature under test
  (executing shell commands).
- `ProcessFinder`/`kill_process` wrap process discovery (`ps`/`lsof`/`ss`) and
  process termination (`kill -9`). The discovery calls are mocked so the
  suite doesn't depend on the host's process table, and the termination path
  (`run_shell("kill -9 <pid>")`) is mocked so the suite never actually kills
  a real process.
- `funshell.kill` imports `farlog.getLogger` at module import time; the
  import tests below confirm that succeeds cleanly.
"""

import subprocess
from unittest.mock import patch


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


def test_process_finder_kill_never_runs_real_kill_command():
    from funshell.kill import ProcessFinder

    finder = ProcessFinder()
    with patch("funshell.kill.run_shell") as mock_run_shell:
        outcomes = finder.kill(pids=[999999])

    mock_run_shell.assert_called_once_with("kill -9 999999")
    assert outcomes == [(999999, True)]


def test_kill_process_with_no_args_is_noop_and_touches_nothing():
    from funshell.kill import kill_process

    # Neither port nor name given -> returns [] before any subprocess call.
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
        patch("funshell.kill.subprocess.run", return_value=completed),
        patch("funshell.kill.run_shell") as mock_run_shell,
    ):
        outcomes = kill_process(name=("myproc",))

    mock_run_shell.assert_called_once_with("kill -9 789")
    assert outcomes == [(789, True)]
