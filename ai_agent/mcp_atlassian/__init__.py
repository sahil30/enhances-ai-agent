"""Integrated MCP Atlassian package for AI Agent"""

import logging
from importlib.metadata import PackageNotFoundError, version

# Set up basic logging
logger = logging.getLogger(__name__)

try:
    __version__ = version("mcp-atlassian")
except PackageNotFoundError:
    # package is not installed
    __version__ = "0.0.0"

# Try to import key modules, but don't fail if they're missing
try:
    from . import models
    from . import utils
    from . import confluence
    from . import jira
    
    # Make commonly used classes available at package level
    __all__ = ['models', 'utils', 'confluence', 'jira', '__version__', 'logger']
    
    logger.info(f"mcp_atlassian package loaded successfully, version {__version__}")
    
except ImportError as e:
    # Graceful degradation if modules are missing
    logger.warning(f"Some mcp_atlassian modules could not be imported: {e}")
    __all__ = ['__version__', 'logger']
