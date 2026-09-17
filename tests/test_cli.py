"""CLI smoke tests for funshell (port/name query + kill), all discovery/kill mocked."""

import subprocess
from unittest.mock import patch

from typer.testing import CliRunner

from funshell.cli import app

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
        patch("funshell.kill.subprocess.run", return_value=completed),
        patch("funshell.kill.run_shell") as mock_run_shell,
    ):
        result = runner.invoke(app, ["port", "8080"])

    assert result.exit_code == 0
    mock_run_shell.assert_not_called()
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
        patch("funshell.kill.subprocess.run", return_value=completed),
        patch("funshell.kill.run_shell") as mock_run_shell,
    ):
        result = runner.invoke(app, ["port", "8080", "--kill"])

    assert result.exit_code == 0
    mock_run_shell.assert_called_once_with("kill -9 42")


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
        patch("funshell.kill.subprocess.run", return_value=completed),
        patch("funshell.kill.run_shell") as mock_run_shell,
    ):
        result = runner.invoke(app, ["name", "myproc", "--kill", "--sig", "TERM"])

    assert result.exit_code == 0
    mock_run_shell.assert_called_once_with("kill -TERM 789")
    assert "pid=789" in result.output
