import os
import sys
import yaml
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Define a logging function that uses print in HTTP mode and stderr in stdio mode


def log(message):
    if os.environ.get("FASTMCP_HTTP") == "1":
        print(message)
    else:
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()


# Load environment variables from .env file
load_dotenv()

# Load the YAML configuration file
CONFIG_PATH = os.environ.get(
    "CONFIG_PATH", "/Users/gregory/g/projects/llm/roma/rfk_jr/rfkjr.yaml")

config = {}

with open(CONFIG_PATH, "r") as file:
    log(f"Loading config from {CONFIG_PATH}")
    config = yaml.safe_load(file)
    log(f"Config loaded: {config}")

# Create the MCP server
mcp = FastMCP(
    "RFK Jr Bridge",
    description="Bridge between MCP and RFK Jr endpoints",
    dependencies=[
        "pyyaml",
        "httpx",
        "pydantic",
    ],
)
mcp.settings.debug = True
mcp.settings.log_level = "DEBUG"

# Dictionary to store OpenAPI schemas for each endpoint
endpoint_schemas = {}


async def fetch_openapi_schema(url: str) -> Dict[str, Any]:
    """Fetch the OpenAPI schema from an endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{url}/openapi.json")
        return response.json()


async def fetch_prompt(url: str) -> Optional[str]:
    """Fetch the prompt from an endpoint if available."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/__prompt__")
            if response.status_code == 200:
                return response.text
            return None
    except Exception:
        return None


async def initialize_endpoints():
    """Initialize the endpoints by fetching their OpenAPI schemas."""
    for endpoint_name, endpoint_config in config.items():
        if endpoint_config.get("url") == "canvas" or endpoint_config.get("url", "").startswith("#"):
            continue

        url = endpoint_config["url"]
        try:
            endpoint_schemas[endpoint_name] = await fetch_openapi_schema(url)

            # Register tools for each endpoint
            register_endpoint_tools(
                endpoint_name, url, endpoint_schemas[endpoint_name])

            # Register prompt if available
            prompt = await fetch_prompt(url)
            if prompt:
                register_endpoint_prompt(endpoint_name, prompt)

        except Exception as e:
            log(f"Error initializing endpoint {endpoint_name}: {e}")
    log(f"Initialized {len(endpoint_schemas)} endpoints")


def register_endpoint_tools(endpoint_name: str, url: str, schema: Dict[str, Any]):
    """Register tools for an endpoint based on its OpenAPI schema."""
    for path, path_item in schema.get("paths", {}).items():
        for method, operation in path_item.items():
            # Check if this operation is marked for CPM
            if "CPM" in operation or "x-CPM" in operation:
                operation_id = operation.get("operationId")
                if not operation_id:
                    continue

                # Create a tool for this operation
                tool_name = f"{endpoint_name}_{operation_id}"

                # Extract parameters
                parameters = []
                if "parameters" in operation:
                    parameters = operation["parameters"]

                # Extract request body schema if present
                request_body_schema = None
                if "requestBody" in operation:
                    content_type = next(
                        iter(operation["requestBody"].get("content", {})), None)
                    if content_type:
                        request_body_schema = operation["requestBody"]["content"][content_type].get(
                            "schema")

                # Register the tool
                register_tool(tool_name, endpoint_name, url, path,
                              method, operation, parameters, request_body_schema)


def register_tool(
    tool_name: str,
    endpoint_name: str,
    url: str,
    path: str,
    method: str,
    operation: Dict[str, Any],
    parameters: List[Dict[str, Any]],
    request_body_schema: Optional[Dict[str, Any]]
):
    """Register a tool for a specific endpoint operation."""

    # Create a dynamic tool function
    async def tool_function(query):
        async with httpx.AsyncClient() as client:
            # Handle path parameters
            formatted_path = path

            # Prepare request
            request_url = f"{url}{formatted_path}"

            # Check if the request expects form-encoded data
            is_form_encoded = False
            if request_body_schema and "content" in operation.get("requestBody", {}):
                content_types = operation["requestBody"]["content"].keys()
                is_form_encoded = any("form" in ct.lower()
                                      for ct in content_types)

            if method.lower() == "get":
                # For GET requests, use query parameters
                response = await client.get(request_url, params=query)
            elif method.lower() == "post":
                if is_form_encoded:
                    # For POST requests with form-encoded data
                    log(f"Sending form data: {query}")
                    response = await client.post(request_url, data=query)
                else:
                    # For POST requests with JSON body
                    response = await client.post(request_url, json=query)
            else:
                # Handle other methods as needed
                response = await client.request(method, request_url, json=query)

            # Return the response
            return response.text

    # Set function metadata
    tool_function.__name__ = tool_name
    operation_id = operation.get("operationId", "unknown")
    tool_function.__doc__ = operation.get(
        "description", f"Call {endpoint_name} {operation_id}")

    # Register the tool with FastMCP
    mcp.tool()(tool_function)


def register_endpoint_prompt(endpoint_name: str, prompt_text: str):
    """Register a prompt for an endpoint."""

    @mcp.prompt()
    def endpoint_prompt() -> str:
        return prompt_text

    # Set function name
    endpoint_prompt.__name__ = f"{endpoint_name}_prompt"

# Add a resource to get the list of available endpoints


@mcp.resource("endpoints://list")
def get_endpoints() -> str:
    """Get a list of available endpoints."""
    result = []
    for endpoint_name, endpoint_config in config.items():
        if endpoint_config.get("url") != "canvas" and not endpoint_config.get("url", "").startswith("#"):
            result.append(f"{endpoint_name}: {endpoint_config['url']}")
    return "\n".join(result)

# Add a tool to get information about a specific endpoint


@mcp.tool()
def get_endpoint_info(endpoint_name: str) -> str:
    """Get information about a specific endpoint."""
    if endpoint_name not in config:
        return f"Endpoint {endpoint_name} not found."

    endpoint_config = config[endpoint_name]
    if endpoint_config.get("url") == "canvas" or endpoint_config.get("url", "").startswith("#"):
        return f"Endpoint {endpoint_name} is not a standard API endpoint."

    schema = endpoint_schemas.get(endpoint_name)
    if not schema:
        return f"Schema for endpoint {endpoint_name} not available."

    # Extract and format endpoint information
    info = schema.get("info", {})
    paths = schema.get("paths", {})

    result = [
        f"Endpoint: {endpoint_name}",
        f"URL: {endpoint_config['url']}",
        f"Title: {info.get('title', 'N/A')}",
        f"Description: {info.get('description', 'N/A')}",
        f"Version: {info.get('version', 'N/A')}",
        "\nAvailable Operations:"
    ]

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if "CPM" in operation or "x-CPM" in operation:
                result.append(
                    f"  - {method.upper()} {path}: {operation.get('summary', 'N/A')}")

    return "\n".join(result)


def main():
    log("Hello, world!")
    asyncio.run(initialize_endpoints())
    if os.environ.get("FASTMCP_HTTP") == "1":
        log("Running in HTTP mode")
        port = int(os.environ.get("PORT", 10000))
        mcp.settings.port = port

        # uvicorn.run(app, host="0.0.0.0", port=port)
        asyncio.run(mcp.run(transport="sse"))
    else:
        # Run in normal mode (stdio)
        log("Running in stdio mode")
        asyncio.run(mcp.run())


if __name__ == "__main__":
    main()
