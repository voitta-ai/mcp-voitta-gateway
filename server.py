import os
import sys
import yaml
import asyncio
import json
from typing import Dict, Any
from fastmcp import FastMCP
from dotenv import load_dotenv
from voitta import VoittaRouter


def log(message):
    """Log a message to stderr and optionally to a file."""
    with open("/tmp/mcp.log", "a") as log_file:
        log_file.write(f"{message}\n")
        log_file.flush()

    if os.environ.get("FASTMCP_HTTP") == "1":
        print(message)
    else:
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()


# Load environment variables from .env file
load_dotenv()

# Load the YAML configuration file
CONFIG_PATH = os.environ.get(
    "CONFIG_PATH", "config/voitta.yaml")

log(f"Loading config from {CONFIG_PATH}")

# Create the MCP server
mcp = FastMCP(
    "Voitta Gateway",
    description="MCP Gateway for Voitta API",
    dependencies=[
        "pyyaml",
        "voitta",
        "pydantic",
    ],
)
mcp.settings.debug = True
mcp.settings.log_level = "DEBUG"

log(f"Initializing Voitta Router with config from {CONFIG_PATH}")
log(f"Broccoli")
voittaRouter = VoittaRouter(CONFIG_PATH)
log(f"Broccoli2")
log(f"Voitta Router initialized: {voittaRouter}")


async def initialize_voitta():
    """Initialize Voitta and register its tools with MCP."""
    log("Initializing Voitta router")

    # Discover MCP tools
    await voittaRouter.discover_mcp_tools()

    # Get all tools
    all_tools = voittaRouter.get_tools()
    log(f"Loaded {len(all_tools)} tools")

    # Register each tool with MCP
    for tool in all_tools:
        register_voitta_tool(tool)


def register_voitta_tool(tool):
    """Register a Voitta tool with MCP."""
    name = tool["function"]["name"]
    description = tool["function"].get(
        "description", f"Execute Voitta tool: {name}")
    parameters = tool["function"].get("parameters", {})

    @mcp.tool()
    async def voitta_tool(**kwargs):
        """Execute a Voitta tool."""
        try:
            log(f"Calling {name} with arguments: {json.dumps(kwargs)}")

            # Create the tool call structure
            tool_call = {
                "tool_name": name,
                "arguments": kwargs
            }

            # Execute the tool
            result = await execute_tool(tool_call)
            return result
        except Exception as e:
            log(f"Error executing Voitta tool {name}: {e}")
            return f"Error: {str(e)}"

    # Set function metadata
    voitta_tool.__name__ = name
    voitta_tool.__doc__ = description

    # Set input schema if available
    if parameters:
        voitta_tool.input_schema = parameters


async def execute_tool(tool_call):
    """Execute a tool using the VoittaRouter."""
    tool_name = tool_call["tool_name"]
    arguments = tool_call["arguments"]

    # This is a simplified example - in a real implementation, you would use
    # the appropriate method from VoittaRouter to execute the tool
    try:
        # Create a list of tools to execute
        tools_to_execute = [
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": json.dumps(arguments)
                }
            }
        ]

        # Execute the tool
        result = await voittaRouter.execute_tools(tools_to_execute)
        return result
    except Exception as e:
        log(f"Error executing tool {tool_name}: {e}")
        raise


@mcp.resource("voitta://tools")
def get_voitta_tools() -> str:
    """Get a list of available Voitta tools."""
    try:
        all_tools = voittaRouter.get_tools()
        result = ["Available Voitta Tools:"]

        for tool in all_tools:
            name = tool["function"]["name"]
            description = tool["function"].get(
                "description", "No description available")
            result.append(f"- {name}: {description}")

        return "\n".join(result)
    except Exception as e:
        log(f"Error getting Voitta tools: {e}")
        return f"Error retrieving tools: {str(e)}"


@mcp.tool()
def get_voitta_tool_info(tool_name: str) -> str:
    """Get detailed information about a specific Voitta tool."""
    try:
        all_tools = voittaRouter.get_tools()

        # Find the tool with the matching name
        tool_info = None
        for tool in all_tools:
            if tool["function"]["name"] == tool_name:
                tool_info = tool
                break

        if not tool_info:
            return f"Tool '{tool_name}' not found."

        # Extract tool information
        function_info = tool_info["function"]
        description = function_info.get(
            "description", "No description available")
        parameters = function_info.get("parameters", {})

        result = [
            f"Tool: {tool_name}",
            f"Description: {description}",
        ]

        # Add parameter information
        if parameters and "properties" in parameters:
            result.append("\nParameters:")
            properties = parameters["properties"]
            required = parameters.get("required", [])

            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "No description")
                req_status = "Required" if param_name in required else "Optional"
                result.append(
                    f"  - {param_name} ({param_type}, {req_status}): {param_desc}")

        return "\n".join(result)
    except Exception as e:
        log(f"Error getting info for tool {tool_name}: {e}")
        return f"Error retrieving tool info: {str(e)}"


def main():
    log("Starting Voitta MCP Gateway")
    asyncio.run(initialize_voitta())

    if os.environ.get("FASTMCP_HTTP") == "1":
        log("Running in HTTP mode")
        port = int(os.environ.get("PORT", 10000))
        mcp.settings.port = port
        asyncio.run(mcp.run(transport="sse"))
    else:
        # Run in normal mode (stdio)
        log("Running in stdio mode")
        asyncio.run(mcp.run())


log(f"Imported as {__name__}")
if __name__ == "__main__":
    main()
else:
    log("Running with inspector")
    # Use asyncio.run() to properly await the coroutines
    asyncio.run(initialize_voitta())
    asyncio.run(mcp.run())
