# T-Zero Context Engine MCP Server Dockerfile for Glama and Container Deployments
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr (crucial for MCP stdio JSON-RPC transport)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for efficient layer caching
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository code
COPY . .

# Install package so tzero-mcp is registered on system PATH
RUN pip install --no-cache-dir .

# Launch T-Zero MCP Server over stdio
ENTRYPOINT ["python", "-u", "tzero_mcp.py", "--stdio"]
