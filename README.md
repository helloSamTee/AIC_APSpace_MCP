1. Create a .env file under your root project directory as below
```
# .env file
GOOGLE_GENAI_USE_VERTEXAI=FALSE 
GOOGLE_API_KEY= "YOUR-API-KEY"
```
2. Install all dependencies using either `pyproject.toml` or `requirements.txt`
3. Run locally host MCP server with the terminal command `python mcp_server.py`
4. Run gemini agent in another terminal using comand `adk web`