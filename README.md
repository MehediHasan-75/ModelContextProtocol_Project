# 🌐 ModelContextProtocol_Project

A project that uses LangChain with multiple MCP servers via Docker and native Python for tool-based reasoning agents like search, file I/O, and weather reporting.

---

## 📁 Project Structure

> Add project structure details here.

---

## 🐳 How to Set Up Docker Desktop (Ubuntu)

### ✅ Step 1: Create Setup Script

```
cd ~
sudo apt install gnome-terminal

cd Downloads
touch install_docker.sh
ls -al install_docker.sh        # Check permissions
chmod +x install_docker.sh      # Make it executable
ls -al install_docker.sh        # Confirm
code install_docker.sh          # Open in VS Code
```

### ✍️ Paste into `install_docker.sh`

```
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
```

### 🚀 Run the Script

```
./install_docker.sh
```

---

### ✅ Step 2: Download Docker DEB Package

Download from:  
https://docs.docker.com/desktop/setup/install/linux/ubuntu/

---

### ✅ Step 3: Install the Package

```
sudo apt-get update
sudo apt-get install ./docker-desktop-amd64.deb
```

---

### ✅ Step 4: Launch Docker

```
systemctl --user start docker-desktop
```

---

## 🧱 Initialize Docker Containers for Servers

### If Dockerfile Exists

Navigate to the directory (e.g., `server_ref`) and build the Docker image:

```
docker build -t terminal_server_docker .
```

### If Dockerfile Does NOT Exist

```
touch Dockerfile
pip freeze > requirements.txt
```

Then write your Dockerfile accordingly and build.

---

## 🧩 Configure MCP Servers (JSON)

```
{
  "mcpServers": {
    "terminal_server": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--init",
        "-e", "DOCKER_CONTAINER=true",
        "-v", "/home/mehedi/mcp/workspace:/root/mcp/workspace",
        "terminal_server_docker"
      ]
    },
    "weather_server": {
      "command": "python",
      "args": ["/home/mehedi/mcp/servers/weather_server/weather.py"]
    },
    "fetch": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp_fetch_server_test"]
    },
    "brave-search": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "BRAVE_API_KEY=", "mcp/brave-search"
      ],
      "env": {
        "BRAVE_API_KEY": ""
      }
    }
  }
}
```

---

## 🚦 Running the MCP Client

```
uv run langchain_mcp_client_wconfig.py
```

---

## 🔍 Project Use Case

Use multiple MCP servers to:
- Search the web with Brave
- Fetch weather information
- Perform terminal commands and file operations
- fetch data from a link
---

## 🧠 LangChain ReAct Agent in Action

### 🔁 Example User Query

"Search 5 states of United States and get their weather. Save to weather_now.txt"

### ReAct Thought Process

```
Thought: I need to list 5 US states.
Action: brave_search
Action Input: "List 5 states in USA"

Observation: ["California", "Texas", "Florida", "New York", "Illinois"]

Thought: Get the weather for each state.
Action: get_weather("California")
...

Thought: Save results to file.
Action: write_file("weather_now.txt", content)
```

---

## 🛠️ Tool Execution Flow

1. User enters query
2. LangChain constructs prompt using tools
3. LLM chooses a tool
4. Tool bound to MCP server via stdin/stdout
5. LangChain executes tool
6. Result returned and agent continues until done

---

## 📦 How LangChain Executes Tools

```
Tool(
  name="get_weather",
  description="Gets weather for a location",
  func=lambda input: session.invoke_tool("get_weather", input)
)
```

Each tool communicates with its server via:

```
stdin → MCP Server → stdout
```

---

## 📡 Example MCP Server Response

```
{
  "type": "tool_result",
  "tool_name": "brave_search",
  "output": ["California", "Texas", "Florida", "New York", "Illinois"]
}
```

---

## ✅ Final Agent Output

Weather data successfully saved to `weather_now.txt`

---

## 📚 Summary: Tool-to-Server Communication

```
[ LangChain Tool ]
       ↓
[ ClientSession ]
       ↓
stdin / stdout
       ↓
[ MCP Server ]
```

---
