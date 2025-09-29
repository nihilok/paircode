import unittest
from src.paircode.shell_service import ShellService


class TestShellService(unittest.TestCase):

    def test_execute_in_shell_successful_command(self):
        # Test with a simple command that should succeed
        command = 'echo Hello, world!'
        expected_output = 'Hello, world!\n'
        result = ShellService.execute_in_shell(command)
        self.assertEqual(result, expected_output)

    def test_execute_in_shell_failed_command(self):
        # Test with a command that should fail
        command = 'non_existent_command'
        result = ShellService.execute_in_shell(command)
        self.assertTrue('Error executing command' in result)

    def test_execute_in_shell_empty_command(self):
        # Test with an empty command
        command = ''
        result = ShellService.execute_in_shell(command)
        self.assertTrue('Error executing command' in result)

    def test_execute_in_shell_command_with_no_output(self):
        # Test with a command that produces no output
        command = 'true'
        expected_output = ''
        result = ShellService.execute_in_shell(command)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
