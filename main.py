#!/usr/bin/env python3
"""
Main entry point for AI Agent CLI

This script provides command-line access to the AI Agent functionality.
Use this for interactive queries, batch processing, and system administration.

Examples:
    python main.py search "authentication issues"
    python main.py batch-search queries.txt
    python main.py config-check
    python main.py analyze-repo --repo-path ./my-code
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agent.api.cli import main

if __name__ == "__main__":
    main()