# MCP Gateway for RFK Jr Endpoints

This is available to run using both STDIO and SSE transports

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

### Running from the Command Line

### Testing with MCP Inspector:


Start [MCP inspector](https://github.com/modelcontextprotocol/inspector) with:

```
npx @modelcontextprotocol/inspector
```

For STDIO, go to the inspector console at http://localhost:5173 and use:

|Transport Type|STDIO|
|Command|`uv`|
|Arguments|`run --with fastmcp --with pyyaml --with httpx --with pydantic fastmcp run server.py`|

## Installation

### Install for Claude

### Install for Cline
