import subprocess
import sys

def test_cli_start():
    result = subprocess.run([sys.executable, '-m', 'paircode.cli'], input=b'\n\n\n', capture_output=True)
    assert b'Welcome to PairCode!' in result.stdout
    assert b'Session complete!' in result.stdout

