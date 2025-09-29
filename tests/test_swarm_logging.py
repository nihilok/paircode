import logging
from paircode.agents import create_paircode_swarm

# Configure logging to capture the log outputs for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def test_swarm_logging():
    # Create the swarm app
    app = create_paircode_swarm('Coder', 'Tester')
    
    def log_capture():
        log_output = []

        class ListHandler(logging.Handler):
            def emit(self, record):
                log_output.append(self.format(record))

        handler = ListHandler()
        logger.addHandler(handler)

        return log_output
    
    # Capture the logs
    log_output = log_capture()
    
    # Execute a simple operation to trigger logging
    # This can be replaced with a specific operation to test
    app.run_some_operation()  # You would replace this with an actual method call

    # Check if logging output captured expected initial logs
    assert any("supervisor" in log for log in log_output), "Expected log output for supervisory actions"
    assert any("coder" in log for log in log_output), "Expected log output for coder actions"
    assert any("tester" in log for log in log_output), "Expected log output for tester actions"

# The test should be run using a test runner like pytest or unittest
