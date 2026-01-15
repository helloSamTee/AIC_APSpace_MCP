# File agent.py
import functools
import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import (
    InMemoryArtifactService,  # Optional
)
from google.adk.models.google_llm import Gemini

from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
)
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams
from google.genai import types
from rich import print
load_dotenv()

# import msal

# def get_ms_token():
#     client_id = os.getenv("MS_CLIENT_ID")
#     tenant_id = os.getenv("MS_TENANT_ID")
#     authority = f"https://login.microsoftonline.com/{tenant_id}"
#     # Use the scope required by your specific API
#     scopes = ["User.Read"] 

#     cache = msal.SerializableTokenCache()
#     cache_path = "token_cache.bin"

#     if os.path.exists(cache_path):
#         with open(cache_path, "r") as f:
#             cache.deserialize(f.read())

#     app = msal.PublicClientApplication(client_id, authority=authority, token_cache=cache)
    
#     accounts = app.get_accounts()
#     result = None

#     if accounts:
#         # Try to get the token silently from cache
#         result = app.acquire_token_silent(scopes, account=accounts[0])

#     if not result:
#         # First time login or cache expired: opens browser
#         result = app.acquire_token_interactive(scopes=scopes)
#         with open(cache_path, "w") as f:
#             f.write(cache.serialize())

#     return result.get("access_token")

def get_tools_async():
    """Gets tools from the File System MCP Server."""
    bearer_token = os.environ["BEARER_TOKEN"]
    
    tools = McpToolset(
        connection_params=SseServerParams(
            url="http://localhost:3333/sse",
        )
    )
    
    # Capture the original async get_tools method
    original_get_tools = tools.get_tools

    async def wrapped_get_tools(*args, **kwargs):
        # 1. Get the list of McpTool objects
        tools = await original_get_tools(*args, **kwargs)
        
        for tool in tools:
            # 2. Capture the original run_async method
            original_run_async = tool.run_async

            # 3. Define the wrapper for the execution logic
            @functools.wraps(original_run_async)
            async def wrapped_run_async(args: dict, tool_context):
                # We inject 'jwt_token' into the arguments dict 
                # before it's sent to the MCP server
                args["jwt_token"] = bearer_token
                
                return await original_run_async(args=args, tool_context=tool_context)

            # 4. Replace the method on the tool instance
            tool.run_async = wrapped_run_async
            
        return tools

    # Override the instance method
    tools.get_tools = wrapped_get_tools
        
    print("MCP Toolset created with automatic token injection.")
    return tools

def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    tools = get_tools_async()
    # print(f"Fetched {len(tools)} tools from MCP server.")
    
    retry_config = types.HttpRetryOptions(
        attempts=5,  # Maximum retry attempts
        exp_base=7,  # Delay multiplier
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
    )
    
    root_agent = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
        name="APSpaceAgent",
        tools=[tools],
    )
    return root_agent

root_agent = get_agent_async()