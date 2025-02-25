# MCP Gateway for RFK Jr Endpoints

This project creates an MCP (Model Context Protocol) server that bridges functionality between MCP and the endpoints described in the RFK Jr YAML configuration file.

## Overview

The MCP Gateway dynamically discovers and exposes tools and resources from the endpoints defined in the RFK Jr YAML configuration file. It acts as a bridge between MCP-compatible clients (like Claude Desktop or Cline) and the RFK Jr endpoints.

## Features

- Dynamically discovers endpoints from the YAML configuration file
- Automatically registers tools based on OpenAPI schemas
- Exposes prompts from endpoints if available
- Provides tools to list and get information about available endpoints

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The server reads the endpoint configuration from a YAML file. By default, it looks for the file at `/Users/gregory/g/projects/llm/roma/rfk_jr/rfkjr.yaml`, but you can specify a different path using the `CONFIG_PATH` environment variable.

Example YAML configuration:
```yaml
inna_cpt:
    url: http://127.0.0.1:7001

canvas:
    url: canvas
```

## Usage

### Running with VSCode

Four launch configurations are provided in `.vscode/launch.json`:

1. **FastMCP Dev Server (Direct)**: Runs the server in development mode with the MCP Inspector by directly running the server.py file. This is the recommended way to run the server during development as it allows for debugging with breakpoints.
2. **FastMCP Dev Server (CLI)**: Runs the server in development mode with the MCP Inspector using the fastmcp CLI.
3. **HTTP Server**: Runs the server as an HTTP server, exposing a REST API for interaction.
4. **Run Server Directly**: Runs the server in stdio mode without the MCP Inspector or HTTP server.

### Running from the Command Line

#### Development Mode (with MCP Inspector)

```bash
# Using the fastmcp CLI (recommended)
fastmcp dev server.py
```

When running with the fastmcp CLI, the server will start a web interface with the MCP Inspector where you can test your server interactively.

Note: The built-in development mode (`FASTMCP_DEV=1 python server.py`) will run the server in stdio mode and display a message recommending to use the fastmcp CLI for the full development experience.

#### HTTP Server Mode

```bash
# Run as an HTTP server
FASTMCP_HTTP=1 python server.py
```

When running in HTTP server mode, the server will start a REST API on the port specified in the `.env` file (default: 10000). This allows you to interact with the server via HTTP requests, which can be useful for integration with other services or for testing with tools like curl or Postman.

#### Stdio Mode (Default)

```bash
python server.py
```

When running in stdio mode (without FASTMCP_DEV=1 or FASTMCP_HTTP=1), the server uses stdio for communication rather than a specific port. This is the standard behavior for MCP servers when they're not in development or HTTP mode, and is how they communicate with Claude Desktop or Cline.

### Installing for Claude Desktop or Cline

```bash
fastmcp install server.py
```

## How It Works

1. The server loads the YAML configuration file
2. For each endpoint, it fetches the OpenAPI schema
3. It registers tools for each operation marked with `CPM` or `x-CPM` in the OpenAPI schema
4. It fetches and registers prompts from endpoints if available
5. It provides additional tools to list and get information about available endpoints

## Available Tools and Resources

### Resources

- `endpoints://list`: Lists all available endpoints

### Tools

- `get_endpoint_info`: Gets detailed information about a specific endpoint
- Dynamic tools from endpoints: Tools are dynamically registered based on the OpenAPI schemas of the endpoints

## Development

To add new features or modify the server:

1. Edit `server.py`
2. Run the server in development mode to test your changes
3. Update the documentation as needed
