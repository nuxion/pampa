from typing import Dict, Any
import subprocess
schema = {
    "type": "function",
    "name": "bash_run",
    "description": "Execute a shell command in a restricted environment and return stdout, stderr, and exit code.",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute."
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum time in seconds to allow the command to run.",
                "minimum": 0
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for command execution."
            },
            "max_output_bytes": {
                "type": "integer",
                "description": "Maximum number of bytes to return for stdout+stderr.",
                "minimum": 0
            },
            "capture_stderr": {
                "type": "boolean",
                "description": "Whether to capture standard error in the output."
            }
        },
        "required": ["command"],
        "additionalProperties": False
    }
}

FORBIDDEN_PATTERNS = [
    "rm -rf /", "shutdown", "reboot", "mkfs", "dd if=", "passwd", "sudo", "su "
]

def run_bash_command(command: str, timeout: int = 10, cwd: str | None = None,
                     max_output_bytes: int | None = None, capture_stderr: bool = True) -> Dict[str, Any]:
    # Basic policy check to reject obviously dangerous patterns
    if any(pat in command for pat in FORBIDDEN_PATTERNS):
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command rejected by safety policy."
        }

    env = {"PATH": "/usr/bin:/bin", "HOME": "/home/sandbox"}
    try:
        # Use a restricted shell to interpret the command
        completed = subprocess.run(
            ["/bin/bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        stdout = completed.stdout
        stderr = completed.stderr if capture_stderr else ""
        # Apply max_output_bytes if requested
        if max_output_bytes is not None:
            data = (stdout or "") + (stderr or "")
            if len(data) > max_output_bytes:
                cut = max_output_bytes
                stdout = (stdout or "")[:cut]
                stderr = (stderr or "")[: (cut - len(stdout))] if cut > len(stdout) else ""
        return {
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.TimeoutExpired as e:
        return {"exit_code": -1, "stdout": e.stdout or "", "stderr": "Command timed out."}
