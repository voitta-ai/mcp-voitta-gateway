#!/bin/bash

set -x

FACTMCP=$(which fastmcp)

SERVER_PY=$(dirname $0)/../server.py


npx @modelcontextprotocol/inspector node build/index.js \
  -e foo=bar \
  $FACTMCP run $SERVER_PY