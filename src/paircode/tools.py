import os

from langchain_core.tools import BaseTool
from langgraph_swarm import create_handoff_tool

from paircode.file_service import FileService
from paircode.shell_service import ShellService


class HandoffTools:
    @staticmethod
    def hand_off_to_coder(name: str) -> BaseTool:
        return create_handoff_tool(
            agent_name=name,
            description=f"Transfer to {name} to write the code.",
        )

    @staticmethod
    def hand_off_to_tester(name: str) -> BaseTool:
        return create_handoff_tool(
            agent_name=name,
            description=f"Transfer to {name} to write or run tests.",
        )

    @staticmethod
    def hand_off_to_supervisor(name: str) -> BaseTool:
        return create_handoff_tool(
            agent_name=name,
            description=f"Transfer to {name} for coordination.",
        )

    @staticmethod
    def end_session() -> BaseTool:
        """Tool to end the session when the task is complete and the definition of done is met."""
        return "Session ended. Good job everyone! The definition of done has been met."


class FileSystemTools:
    file_service = FileService(os.getcwd())
    shell_service = ShellService()

    @classmethod
    def read_file(cls, path: str) -> str:
        """Read text content from a file."""
        return cls.file_service.read_file(path)

    @classmethod
    def write_to_file(cls, path: str, content: str) -> str:
        """Write text content to a file."""
        return cls.file_service.write_to_file(path, content)

    @classmethod
    def list_files(cls, directory: str) -> str:
        """List files in a directory."""
        return cls.file_service.list_files(directory)

    @classmethod
    def execute_in_shell(cls, command: str) -> str:
        """Execute a shell command and return the output."""
        return cls.shell_service.execute_in_shell(command)
