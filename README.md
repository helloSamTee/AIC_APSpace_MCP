# Environment Setup
This project uses uv for fast, reliable dependency management. Follow these steps to set up your local development environment.

1. Prerequisites
Ensure you have uv installed on your system. It replaces pip and manages virtual environments automatically.
```
pip install uv
```

2. Dependency Installation
Run the following command to create a virtual environment and install all required packages (including google-adk and fastmcp) exactly as specified in the lockfile:
```
uv sync
```
This command creates a .venv folder in your project root.

3. .env file creation
1. Create a .env file under your root project directory as below
```
# .env file
GOOGLE_GENAI_USE_VERTEXAI=FALSE 
GOOGLE_API_KEY= "YOUR-API-KEY"
BEARER_TOKEN = 'YOUR-BEARER-TOKEN'
X_API_KEY = "YOUR-X-API-KEY"
```
  
# Running the Application
uv allows you to run scripts within the virtual environment without manual activation using the uv run command.

Step 1: Start the MCP Server
Open a terminal and start the tool server
```
uv run python server/mcp_server.py
```
OR 
```
python server/mcp_server.py
```

Step 2: Start the ADK Agent
Open a second terminal and launch the AI Agent interface:
```
uv run adk web .
```
OR 
```
adk web
```

Step 3: Select agent `basic` in the adk UI

