# MCP Gateway for Voitta

This MCP server provides a gateway to the Voitta library, allowing you to use Voitta's capabilities through the Model Context Protocol (MCP). It supports both STDIO and SSE transports.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt` (including voitta)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The server reads the Voitta configuration from a YAML file. By default, it looks for the file at `/Users/gregory/g/projects/llm/roma/voitta-example/config/voitta.yaml`, but you can specify a different path using the `CONFIG_PATH` environment variable.

The configuration file should follow the format expected by the Voitta library. Refer to the [Voitta documentation](https://pypi.org/project/voitta/) for details on the configuration format.

## Usage

### Running with VSCode

You can run the server directly from VSCode using the provided launch configuration.

### Running from the Command Line

Run the server using:

```bash
python server.py
```

For HTTP mode (SSE transport):

```bash
FASTMCP_HTTP=1 PORT=10000 python server.py
```

### Testing with MCP Inspector

The MCP Inspector is a useful tool for testing and debugging MCP servers. Here's how to use it with the Voitta Gateway:

1. Start the MCP Inspector:
   ```bash
   npx @modelcontextprotocol/inspector
   ```

2. Open the inspector console at http://localhost:5173

3. For STDIO transport (recommended for testing), use one of these options:



   **Option 1: Using python directly**
   - Select "STDIO" as the Transport Type
   - Set the Command to: `python` (or `python3` depending on your system)
   - Set the Arguments to: `server.py`

   **Option 2: Using uv**
   - Select "STDIO" as the Transport Type
   - Set the Command to: `uv`
   - Set the Arguments to: `run --with fastmcp --with pyyaml --with voitta --with pydantic server.py`

   **Option 3: Using fastmcp with full paths**
   - Select "STDIO" as the Transport Type
   - Set the Command to: `/path/to/your/fastmcp` (e.g., `/Users/gregory/g/projects/llm/roma/mcp-voitta-gateway/.venv/bin/fastmcp`)
   - Set the Arguments to: `run /full/path/to/server.py` (e.g., `run /Users/gregory/g/projects/llm/roma/mcp-voitta-gateway/server.py`)
   
   **Option 4: Using cd and fastmcp**
   - Select "STDIO" as the Transport Type
   - Set the Command to: `bash` (or your shell)
   - Set the Arguments to: `-c "cd /Users/gregory/g/projects/llm/roma/mcp-voitta-gateway && fastmcp run server.py"`

4. Click "Connect" to establish a connection to the server

5. Once connected, you can:
   - View available tools under the "Tools" tab
   - Access the `voitta://tools` resource to see all Voitta tools
   - Test tools by providing input parameters and executing them
   - View the server logs in the console output

For HTTP/SSE transport:
1. Start the server in HTTP mode:
   ```bash
   FASTMCP_HTTP=1 PORT=10000 python server.py
   ```
2. In the MCP Inspector, select "SSE" as the Transport Type
3. Set the URL to: `http://localhost:10000`
4. Click "Connect"

## Available Tools and Resources

The server automatically registers all tools provided by the Voitta library. You can get a list of available tools using the `voitta://tools` resource.

Additionally, the server provides the following MCP tools:

- `get_voitta_tool_info`: Get detailed information about a specific Voitta tool, including its parameters and descriptions.

## Installation for LLM Assistants

### Install for Claude

```bash
fastmcp install server.py --name "voitta-gateway"
```

### Install for Cline

Follow the Cline documentation for installing MCP servers.
