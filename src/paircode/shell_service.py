class ShellService:
    @classmethod
    def execute_in_shell(cls, command: str) -> str:
        """Execute a shell command and return the output."""
        if not command.strip():
            return "Error executing command: No command provided"

        import subprocess
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Error executing command: {e.stderr}"