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

# Make basic info available without importing submodules to avoid circular imports
__all__ = ['__version__', 'logger']

logger.info(f"mcp_atlassian package loaded successfully, version {__version__}")

# Lazy import function to avoid circular imports
def get_models():
    """Lazy import of models module"""
    try:
        from . import models
        return models
    except ImportError as e:
        logger.warning(f"Could not import models: {e}")
        return None

def get_utils():
    """Lazy import of utils module"""
    try:
        from . import utils
        return utils
    except ImportError as e:
        logger.warning(f"Could not import utils: {e}")
        return None

def get_confluence():
    """Lazy import of confluence module"""
    try:
        from . import confluence
        return confluence
    except ImportError as e:
        logger.warning(f"Could not import confluence: {e}")
        return None

def get_jira():
    """Lazy import of jira module"""
    try:
        from . import jira
        return jira
    except ImportError as e:
        logger.warning(f"Could not import jira: {e}")
        return None
