# 🧠 Key Project Learnings

* **MCP as a Standardized Interface**: Model Context Protocol (MCP) serves as a vital "handshake" between an AI agent's reasoning and real-world data. It standardizes how tools are exposed, making them modular and reusable across different agents.
* **Decoupled Authentication (Token Forwarding)**: A major finding was that the MCP server should act as a **secure proxy**, not an identity provider. "auth forwarding" is implemented, where the agent retrieves a user's **Bearer JWT** (via .env/ Microsoft SSO) and passes it to the MCP server, which then forwards it to the APSpace APIs. Authentication tokens are automatically injected into the tool calls without the LLM needing to "know" or hallucinate the token string.
* **API Pattern Variations**: Learned to handle multiple API styles within a single server, including **REST (GET)** for timetables and **GraphQL (POST)** for attendance systems like Attendix.

---

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
  
  ---

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

---

### 🔄 Alternative Architectural Paths

While the current system uses a **Google ADK Agent + a Standalone FastMCP Server**, there are several alternative ways this could have been built:

| Alternative | Description | Pros/Cons |
| --- | --- | --- |
| **Google ADK (No Server)** | Define all tools as local Python functions directly inside the `LlmAgent` code. | **Pros**: Simplest setup; no network latency between agent and tools. **Cons**: Harder to scale; tools cannot be reused by other agents. |
| **LangChain MCP** | Use LangChain's built-in MCP integration (originally suggested for a 1-day sprint). | **Pros**: Massive ecosystem of existing integrations. **Cons**: Can have more deployment overhead for simple toolsets. |
| **LangGraph** | A stateful orchestration framework for building complex, multi-agent workflows. | **Pros**: Ideal for long-running tasks or "loops" (e.g., retrying attendance if OTP fails). **Cons**: Significantly higher learning curve and complexity for simple API calls. |

---

### ⚖️ Why Build It This Way? (Standalone MCP Server)

Despite simpler alternatives, the decision to use a standalone **FastMCP Server** was intentional for several reasons:

* **Learning "Enterprise-Style" Architecture**: By building a separate server and client, you learned about **loose coupling**. In a professional environment, one central MCP server could serve a web bot, a mobile app, and a Slack bot simultaneously, which isn't possible if tools are hard-coded into a single agent.
* **Separation of Concerns**: This architecture keeps the **AI Logic** (Google ADK) separate from the **API Logic** (FastMCP). If APSpace changes its API endpoint, you only update the MCP server; you don't need to redeploy the entire AI Agent.
* **Scalability & Remote Hosting**: This setup creates a natural path to host the MCP server on a remote platform like **DigitalOcean**, allowing the tools to be available globally while the agent runs locally or in the cloud.
* **Standardization**: Using FastMCP forces the team to adhere to the official MCP protocol. This means your APSpace tools could theoretically be plugged into **Claude Desktop** or other MCP-compatible clients with almost zero code changes.