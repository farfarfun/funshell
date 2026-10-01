"""CLI smoke tests for funshell (port/name query + kill), all discovery/kill mocked."""

import subprocess
from unittest.mock import patch

from typer.testing import CliRunner

from funshell.cli import app
from funshell.kill import ProcInfo, ProcessFinder

runner = CliRunner()


def test_port_query_no_kill():
    fake_lsof_output = (
        "COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME\n"
        "python  42   user   3u  IPv4 12345      0t0  TCP *:8080 (LISTEN)\n"
    )
    completed = subprocess.CompletedProcess(
        args=["lsof"], returncode=0, stdout=fake_lsof_output, stderr=""
    )
    with (
        patch("funshell.kill.subprocess.run", return_value=completed) as mock_run,
    ):
        result = runner.invoke(app, ["port", "8080"])

    assert result.exit_code == 0
    assert mock_run.call_count == 1
    assert "pid=42" in result.output
    assert "port=8080" in result.output


def test_port_query_with_kill():
    fake_lsof_output = (
        "COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME\n"
        "python  42   user   3u  IPv4 12345      0t0  TCP *:8080 (LISTEN)\n"
    )
    completed = subprocess.CompletedProcess(
        args=["lsof"], returncode=0, stdout=fake_lsof_output, stderr=""
    )
    with (
        patch("funshell.kill.subprocess.run", return_value=completed) as mock_run,
    ):
        result = runner.invoke(app, ["port", "8080", "--kill"])

    assert result.exit_code == 0
    assert mock_run.call_args_list[-1].args[0] == ["kill", "-9", "42"]


def test_port_query_no_match():
    empty = subprocess.CompletedProcess(
        args=["lsof"], returncode=1, stdout="", stderr=""
    )
    with patch("funshell.kill.subprocess.run", return_value=empty):
        result = runner.invoke(app, ["port", "9999"])

    assert result.exit_code == 0
    assert "no matching process found" in result.output


def test_name_query_with_kill():
    fake_ps_output = (
        "  PID COMMAND         COMMAND\n  789 myproc          myproc --run\n"
    )
    completed = subprocess.CompletedProcess(
        args=["ps"], returncode=0, stdout=fake_ps_output, stderr=""
    )
    with (
        patch("funshell.kill.subprocess.run", return_value=completed) as mock_run,
    ):
        result = runner.invoke(app, ["name", "myproc", "--kill", "--sig", "TERM"])

    assert result.exit_code == 0
    assert mock_run.call_args_list[-1].args[0] == ["kill", "-15", "789"]
    assert "pid=789" in result.output


def test_kill_failure_exits_nonzero():
    finder = ProcessFinder()
    finder.procs = [ProcInfo(pid=42, name="python", cmd="python")]
    with (
        patch("funshell.cli.ProcessFinder.find_by_port", return_value=finder),
        patch("funshell.kill._run") as mock_run,
    ):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["kill"], returncode=1, stdout="", stderr="not permitted"
        )
        result = runner.invoke(app, ["port", "8080", "--kill"])

    assert result.exit_code == 1
    assert "PID(s) 42" in result.output


def test_invalid_signal_is_rejected_without_running_kill():
    finder = ProcessFinder()
    finder.procs = [ProcInfo(pid=42, name="python", cmd="python")]
    with (
        patch("funshell.cli.ProcessFinder.find_by_port", return_value=finder),
        patch("funshell.kill._run") as mock_run,
    ):
        result = runner.invoke(app, ["port", "8080", "--kill", "--sig", "9; id"])

    assert result.exit_code != 0
    assert "invalid signal" in result.output
    mock_run.assert_not_called()
