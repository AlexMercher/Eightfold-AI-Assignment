import os
import subprocess
import sys
import pytest

def test_pipeline_stats_dry_run():
    # If there is no run-dir, it should fail gracefully or say not found
    res = subprocess.run([sys.executable, "cli.py", "stats", "--run-dir", "non_existent_dir"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "No statistics found" in res.stdout

def test_pipeline_config_dry_run():
    res = subprocess.run([sys.executable, "cli.py", "config"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "PIPELINE CONFIGURATION" in res.stdout

def test_full_pipeline_run():
    # Only run this if Master.csv exists
    if not os.path.exists("Master.csv"):
        pytest.skip("Master.csv not found")
        
    res = subprocess.run(
        [sys.executable, "cli.py", "run", "--inputs", "Master.csv", "generated_data/matching_candidates.csv"],
        capture_output=True, text=True
    )
    
    assert res.returncode == 0
    assert "ASSIGNMENT PRESENTATION SUMMARY" in res.stdout
    assert "Generated:" in res.stdout
