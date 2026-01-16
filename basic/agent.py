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

def get_tools_async():
    """Gets tools from the File System MCP Server."""
    # Load bearer token from environment variable (.env file)
    bearer_token = os.environ.get("BEARER_TOKEN")
    
    if not bearer_token:
        raise ValueError("BEARER_TOKEN not found in environment")
    
    # Create MCP toolset connection to the server
    toolset = McpToolset(
        connection_params=SseServerParams(
            url="http://localhost:3333/sse",
        )
    )
    
    # Save reference to the original get_tools method before we modify it
    original_get_tools = toolset.get_tools
    
    # Create a wrapper function that will intercept tool retrieval
    async def wrapped_get_tools(*args, **kwargs):
        # Get all tools from MCP server (get_ap_card_balance, get_staff, etc.)
        tools = await original_get_tools(*args, **kwargs)
        
        # Loop through each tool and modify its run_async method
        for tool in tools:
            # Save the original run_async method for this specific tool
            original_run = tool.run_async
            
            # Create a new run_async that injects the token automatically
            # 
            # WHY WE NEED _orig=original_run and _token=bearer_token:
            # 
            # Imagine you have 3 tools: [tool_A, tool_B, tool_C]
            # 
            # WITHOUT closure (WRONG WAY):
            # async def run_with_token(args, tool_context):
            #     return await original_run(args, tool_context)  # <-- Problem!
            # 
            # When tool_A runs later, original_run points to tool_C's function
            # because the loop already finished and original_run = tool_C.run_async
            # Result: ALL tools call tool_C's function! ❌
            # 
            # WITH closure (CORRECT WAY):
            # async def run_with_token(args, tool_context, _orig=original_run):
            #     return await _orig(args, tool_context)  # <-- Fixed!
            # 
            # _orig=original_run creates a COPY of the value at THIS moment
            # tool_A gets _orig=tool_A.run_async
            # tool_B gets _orig=tool_B.run_async  
            # tool_C gets _orig=tool_C.run_async
            # Result: Each tool calls its OWN function! ✅
            async def run_with_token(args: dict, tool_context, _orig=original_run, _token=bearer_token):
                # Inject jwt_token into the arguments before sending to MCP server
                args["jwt_token"] = _token
                # Call the original function with the modified arguments
                return await _orig(args=args, tool_context=tool_context)
            
            # Replace the tool's run_async with our token-injecting version
            tool.run_async = run_with_token
        
        # Return all modified tools
        return tools
    
    # Replace the toolset's get_tools method with our wrapper
    toolset.get_tools = wrapped_get_tools
    return toolset

def get_agent_async():
    """Creates an ADK Agent equipped with tools from the MCP Server."""
    tools = get_tools_async()
    
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )
    
    root_agent = LlmAgent(
        model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
        name="APSpaceAgent",
        tools=[tools],
        instruction="You are APSpace Assistant. IMPORTANT: The jwt_token/bearer token is automatically provided for all API calls - NEVER ask the user for it. When calling any tool that requires authentication, simply call it without mentioning the token."
    )
    return root_agent

root_agent = get_agent_async()