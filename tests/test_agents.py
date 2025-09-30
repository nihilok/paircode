import pytest
from unittest.mock import Mock, patch, MagicMock
from src.paircode.agents import PaircodeSwarmService, run_tests


def test_run_tests():
    """Test the run_tests function returns expected message."""
    test_file = "test_example.py"
    expected_output = "I don't have the ability to execute code. Please run the tests in your local environment."
    assert run_tests(test_file) == expected_output


def test_paircode_swarm_service_initialization():
    """Test that PaircodeSwarmService initializes correctly."""
    with patch('src.paircode.agents.ChatAnthropic'):
        service = PaircodeSwarmService(
            coder_name="Alice",
            tester_name="Bob",
            supervisor_name="Chief",
            base_directory="."
        )
        
        assert service.coder is not None
        assert service.tester is not None
        assert service.supervisor is not None
        assert service.swarm is not None
        assert service.app is not None
        assert service.checkpointer is not None


def test_paircode_swarm_service_default_supervisor():
    """Test that PaircodeSwarmService uses default supervisor name."""
    with patch('src.paircode.agents.ChatAnthropic'):
        service = PaircodeSwarmService(
            coder_name="Alice",
            tester_name="Bob"
        )
        
        # The service should be created successfully with default supervisor name
        assert service is not None


def test_paircode_swarm_service_stream_method():
    """Test that the stream method exists and is callable."""
    with patch('src.paircode.agents.ChatAnthropic'):
        service = PaircodeSwarmService(
            coder_name="Alice",
            tester_name="Bob",
            supervisor_name="Chief"
        )
        
        # Check that stream method exists
        assert hasattr(service, 'stream')
        assert callable(service.stream)


@patch('src.paircode.agents.ChatAnthropic')
def test_paircode_swarm_service_with_custom_base_directory(mock_anthropic):
    """Test that PaircodeSwarmService accepts custom base directory."""
    service = PaircodeSwarmService(
        coder_name="Alice",
        tester_name="Bob",
        supervisor_name="Chief",
        base_directory="/custom/path"
    )
    
    assert service.file_service is not None


def test_paircode_swarm_service_has_logging_function():
    """Test that the service has a logging function attached."""
    with patch('src.paircode.agents.ChatAnthropic'):
        service = PaircodeSwarmService(
            coder_name="Alice",
            tester_name="Bob"
        )
        
        assert hasattr(service.app, 'logging_function')
        assert callable(service.app.logging_function)
