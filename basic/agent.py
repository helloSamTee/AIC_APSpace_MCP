# File agent.py

import asyncio
import json
from typing import Any

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
    tools = McpToolset(
        connection_params=SseServerParams(
            url="http://localhost:3333/sse",
        )
    )
    print("MCP Toolset created successfully.")
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
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        name="APSpaceAgent",
        # instructions="""
        # You are an APSpace assistant.
        # You can:
        # - Retrieve student timetables
        # """,
        tools=[tools],
    )
    return root_agent

root_agent = get_agent_async()