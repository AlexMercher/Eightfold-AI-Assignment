import subprocess
import sys
import pytest

def test_cli_doctor():
    res = subprocess.run([sys.executable, "cli.py", "doctor"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Doctor check" in res.stdout

def test_cli_version():
    res = subprocess.run([sys.executable, "cli.py", "version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Pipeline" in res.stdout

def test_cli_help():
    res = subprocess.run([sys.executable, "cli.py", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "run" in res.stdout
    assert "visualize" in res.stdout

def test_cli_config():
    res = subprocess.run([sys.executable, "cli.py", "config"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "PIPELINE CONFIGURATION" in res.stdout

def test_cli_stats_missing_dir():
    res = subprocess.run([sys.executable, "cli.py", "stats", "--run-dir", "non_existent_dir_xyz"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "No statistics found" in res.stdout

def test_cli_invalid_command():
    # CLI should show usage error for completely unknown command
    res = subprocess.run([sys.executable, "cli.py", "boguscommand"], capture_output=True, text=True)
    assert res.returncode != 0
