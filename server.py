#!/usr/bin/env python3
"""
MCP Voitta Gateway Server

This server acts as a gateway between MCP clients and the Voitta router,
exposing Voitta tools via the Model Context Protocol (MCP).
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import yaml
import mcp.server
import mcp.server.stdio
import mcp.types as types
from mcp.server import (
    InitializationOptions,
    NotificationOptions,
    Server,
)

# Configure logging to write to file
import os

# Ensure log directory exists
log_dir = "/tmp/mcp-voitta-gateway"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "server.log")

# Set up file handler
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Configure logger
logger = logging.getLogger("mcp-voitta-gateway")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.propagate = False  # Prevent logs from being sent to stderr

# Import VoittaRouter (assuming voitta is installed with pip)
from voitta import VoittaRouter


class VoittaMcpServer:
    """
    MCP Server implementation that exposes Voitta tools via the Model Context Protocol.
    """

    def __init__(self, config_path: str):
        """
        Initialize the Voitta MCP Server.

        Args:
            config_path: Path to the Voitta configuration file.
        """
        self.config_path = config_path
        self.voitta_router = None
        self.server = Server("voitta-gateway")
        self.setup_handlers()

    async def initialize(self):
        """Initialize the Voitta router."""
        try:
            # Initialize the router with the configuration file path directly
            self.voitta_router = VoittaRouter(self.config_path)
            
            # Discover MCP tools if any
            await self.voitta_router.discover_mcp_tools()
            
            logger.info("Initialized Voitta MCP Server")
        except Exception as e:
            logger.error(f"Failed to initialize Voitta MCP Server: {e}")
            raise

    def setup_handlers(self):
        """Set up the MCP request handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """
            Handle a request to list available tools.
            
            Returns:
                List of Tool objects representing the available Voitta tools.
            """

            logger.info("list_tools()")

            if not self.voitta_router:
                logger.error("Voitta router not initialized")
                return []
            
            # Get tools from the Voitta router
            voitta_tools = self.voitta_router.get_tools()
            
            

            # Convert Voitta tools to MCP Tool objects
            mcp_tools = []
            for tool in voitta_tools:
                # Extract tool information from the function object
                function_info = tool.get("function", {})
                tool_name = function_info.get("name", "").split("____")[-1]  # Get the actual function name without prefix
                tool_description = function_info.get("description", "")
                tool_parameters = function_info.get("parameters", {})
                
                logger.info(f"tool: {tool_name}")

                # Log the tool parameters for debugging
                logger.info(f"tool_parameters before: {json.dumps(tool_parameters, indent=2)}")
                
                # Create a proper JSON Schema for the input_schema
                # Ensure it has the required 'type' field and other required fields
                input_schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                # If tool_parameters already has the correct structure, use it
                if isinstance(tool_parameters, dict):
                    if 'type' in tool_parameters:
                        input_schema = tool_parameters
                    elif 'properties' in tool_parameters:
                        input_schema['properties'] = tool_parameters.get('properties', {})
                        input_schema['required'] = tool_parameters.get('required', [])
                    else:
                        # If it's a flat dictionary, convert it to properties
                        for key, value in tool_parameters.items():
                            if key not in ['type', 'properties', 'required']:
                                input_schema['properties'][key] = value
                
                logger.info(f"input_schema after: {json.dumps(input_schema, indent=2)}")
                
                # Create MCP Tool object
                mcp_tool = types.Tool(
                    name=tool_name,
                    description=tool_description,
                    inputSchema=input_schema
                )

                logger.info(f"mcp_tool: {mcp_tool}")

                mcp_tools.append(mcp_tool)
            
            logger.info(f"{mcp_tools}")

            return mcp_tools

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any] | None
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """
            Handle a request to call a tool.
            
            Args:
                name: The name of the tool to call.
                arguments: The arguments to pass to the tool.
                
            Returns:
                List of content items representing the result of the tool call.
            """
            if not self.voitta_router:
                logger.error("Voitta router not initialized")
                return [types.TextContent(text="Error: Voitta router not initialized")]
            
            try:
                # Find the full tool name with prefix
                full_tool_name = None
                for tool in self.voitta_router.get_tools():
                    function_name = tool.get("function", {}).get("name", "")
                    if function_name.endswith(f"____{name}"):
                        full_tool_name = function_name
                        break
                
                if not full_tool_name:
                    logger.error(f"Tool {name} not found")
                    return [types.TextContent(text=f"Error: Tool {name} not found")]
                
                # Call the tool through the Voitta router
                # Using empty strings for token and oauth_token as they're not needed for this implementation
                result = await self.voitta_router.call_function(full_tool_name, arguments or {}, "", "")
                
                # Convert the result to MCP format
                if isinstance(result, str):
                    # Text result
                    return [types.TextContent(text=str(result), type="text")]
                elif isinstance(result, dict) or isinstance(result, list):
                    # JSON result
                    return [types.TextContent(text=json.dumps(result, indent=2), type="text")]
                else:
                    # Unknown result type, convert to string
                    return [types.TextContent(text=str(result), type="text")]
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [types.TextContent(text=f"Error calling tool {name}: {str(e)}", type="text")]

    async def run(self):
        """Run the MCP server."""
        # Initialize the Voitta router
        await self.initialize()
        
        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="voitta-gateway",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    """Main entry point for the MCP Voitta Gateway server."""
    parser = argparse.ArgumentParser(description="MCP Voitta Gateway Server")
    parser.add_argument(
        "--config", 
        default="config/voitta.yaml",
        help="Path to the Voitta configuration file"
    )
    args = parser.parse_args()
    
    # Create and run the server
    server = VoittaMcpServer(args.config)
    try:
        logger.info("Starting MCP Voitta Gateway Server")
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
