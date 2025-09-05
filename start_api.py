#!/usr/bin/env python3
"""
Web API Server Entry Point

This script starts the FastAPI web server for the AI Agent.
Use this for web-based access to AI Agent functionality.

Examples:
    python start_api.py
    python start_api.py --host 0.0.0.0 --port 8080
    python start_api.py --debug
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agent.api.web_api import run_server

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agent Web API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)