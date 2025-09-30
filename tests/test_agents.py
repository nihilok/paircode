import pytest
import logging
from src.paircode.agents import write_code, write_tests, run_tests, create_paircode_swarm


# Utility to capture logging output
def capture_logged_output(swarm_app, message):
    with pytest.raises(AssertionError):  # We expect something to be logged, so we make sure no success is claimed.
        with pytest.fail_on_log_level(logging.INFO) as log_capture:
            swarm_app.logging_function(message)
        assert "User Update:" in log_capture.text, "Log capture did not contain expected user update message."


# Existing test cases
def test_write_code():
    task = "Implement a sorting algorithm"
    expected_output = "Code for: Implement a sorting algorithm\n[def foo(): pass]"
    assert write_code(task) == expected_output


def test_write_tests():
    task = "Test sorting algorithm"
    expected_output = "Tests for: Test sorting algorithm\n[def test_foo(): assert True]"
    assert write_tests(task) == expected_output


def test_run_tests():
    code = "def foo(): pass"
    tests = "def test_foo(): assert True"
    expected_output = "All tests passed!"
    assert run_tests(code, tests) == expected_output


def test_create_paircode_swarm():
    # This is a placeholder to ensure the function runs without error
    try:
        swarm_app = create_paircode_swarm("Coder", "Tester")
        capture_logged_output(swarm_app, "Test message.")
    except Exception as e:
        pytest.fail(f"Swarm creation failed with exception: {e}")
