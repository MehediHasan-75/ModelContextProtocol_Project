import os
import subprocess
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP with terminal name
mcp = FastMCP("terminal")

# Set the default workspace path
DEFAULT_WORKSPACE = os.path.expanduser('~/mcp/workspace')
os.makedirs(DEFAULT_WORKSPACE, exist_ok=True)  # Ensure workspace exists

@mcp.tool()
def run_command(command: str) -> str:
    """
    Tool: run_command
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
    """
    Tool: write_file
    Writes or creates a file inside DEFAULT_WORKSPACE with the given content.
    """
    try:
        full_path = os.path.join(DEFAULT_WORKSPACE, filename)
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"✅ File '{filename}' written successfully."
    except Exception as e:
        return f"❌ Failed to write file: {e}"

@mcp.tool()
def edit_file(filename: str, new_content: str) -> str:
    """
    Tool: edit_file
    Overwrites an existing file with new content.

    Inputs:
    - filename (str): Name of the file to edit (must exist in DEFAULT_WORKSPACE)
    - new_content (str): The updated content to replace the file with
    """
    try:
        full_path = os.path.join(DEFAULT_WORKSPACE, filename)
        if not os.path.isfile(full_path):
            return f"❌ File '{filename}' does not exist."
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"✅ File '{filename}' updated successfully."
    except Exception as e:
        return f"❌ Failed to edit file: {e}"

if __name__ == "__main__":
    mcp.run(transport='stdio')
