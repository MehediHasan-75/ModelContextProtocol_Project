import os
import subprocess
import fnmatch
from datetime import datetime
from typing import List, Dict, Union
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP with terminal name
mcp = FastMCP("terminal")

# Set the default workspace path
DEFAULT_WORKSPACE = os.path.expanduser('~/mcp/workspace')
os.makedirs(DEFAULT_WORKSPACE, exist_ok=True)  # Ensure workspace exists

# Utility function

def _validate_path(filename: str) -> str:
    full_path = os.path.abspath(os.path.join(DEFAULT_WORKSPACE, filename))
    if not full_path.startswith(DEFAULT_WORKSPACE):
        raise PermissionError("Access denied: Path outside of workspace.")
    return full_path

@mcp.tool()
def run_command(command: str) -> str:
    """
    Executes a shell command inside the DEFAULT_WORKSPACE directory.
    Returns stdout or stderr.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=DEFAULT_WORKSPACE,
            capture_output=True,
            text=True
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return str(e)

@mcp.tool()
def write_file(filename: str, content: str) -> str:
    try:
        full_path = _validate_path(filename)
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"✅ File '{filename}' written successfully."
    except Exception as e:
        return f"❌ Failed to write file: {e}"

@mcp.tool()
def edit_file(filename: str, new_content: str) -> str:
    try:
        full_path = _validate_path(filename)
        if not os.path.isfile(full_path):
            return f"❌ File '{filename}' does not exist."
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"✅ File '{filename}' updated successfully."
    except Exception as e:
        return f"❌ Failed to edit file: {e}"

@mcp.tool()
def list_files() -> List[str]:
    try:
        files = []
        for root, dirs, filenames in os.walk(DEFAULT_WORKSPACE):
            for name in filenames:
                rel_path = os.path.relpath(os.path.join(root, name), DEFAULT_WORKSPACE)
                files.append(rel_path)
        return files
    except Exception as e:
        return [f"❌ Failed to list files: {e}"]

@mcp.tool()
def read_file(filename: str) -> str:
    try:
        full_path = _validate_path(filename)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"❌ Failed to read file: {e}"

@mcp.tool()
def delete_file(filename: str) -> str:
    try:
        full_path = _validate_path(filename)
        os.remove(full_path)
        return f"✅ File '{filename}' deleted successfully."
    except Exception as e:
        return f"❌ Failed to delete file: {e}"

@mcp.tool()
def get_file_info(filename: str) -> Dict[str, Union[str, int]]:
    try:
        full_path = _validate_path(filename)
        stat = os.stat(full_path)
        return {
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:],
            "is_file": os.path.isfile(full_path),
            "is_directory": os.path.isdir(full_path)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_files(pattern: str) -> List[str]:
    try:
        matched = []
        for root, _, files in os.walk(DEFAULT_WORKSPACE):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), DEFAULT_WORKSPACE)
                if fnmatch.fnmatch(rel_path, pattern):
                    matched.append(rel_path)
        return matched
    except Exception as e:
        return [f"❌ Error: {e}"]

if __name__ == "__main__":
    mcp.run(transport='stdio')
