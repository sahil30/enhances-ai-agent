"""
Context Managers and Resource Management Utilities

This module provides async context managers and utilities for proper resource management
in the AI Agent system, ensuring all connections are properly initialized and cleaned up.
"""
from __future__ import annotations

import asyncio
from typing import AsyncContextManager, AsyncGenerator, Optional, Dict, Any, List
from contextlib import asynccontextmanager
import structlog

from .config import Config, load_config
from .types import AIAgentError, ConfigProtocol


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def ai_agent_context(config: Optional[Config] = None) -> AsyncGenerator['AIAgent', None]:
    """
    Async context manager for AIAgent with automatic resource management.
    
    Usage:
        async with ai_agent_context() as agent:
            response = await agent.process_query("How to fix authentication?")
            
    Args:
        config: Optional configuration object
        
    Yields:
        Initialized AIAgent instance
        
    Raises:
        AIAgentError: If initialization fails
    """
    from .agent import AIAgent  # Import here to avoid circular imports
    
    agent = AIAgent(config)
    
    try:
        logger.info("Initializing AI Agent context")
        await agent.initialize()
        yield agent
    except Exception as e:
        logger.error("AI Agent context initialization failed", error=str(e))
        raise AIAgentError(f"Agent context initialization failed: {e}") from e
    finally:
        logger.info("Cleaning up AI Agent context")
        await agent.close()


@asynccontextmanager
async def batch_agent_context(
    configs: List[Config],
    max_concurrent: int = 3
) -> AsyncGenerator[List['AIAgent'], None]:
    """
    Context manager for multiple AI agents with controlled concurrency.
    
    Args:
        configs: List of configurations for each agent
        max_concurrent: Maximum concurrent agent operations
        
    Yields:
        List of initialized AIAgent instances
    """
    from .agent import AIAgent
    
    agents: List[AIAgent] = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def init_agent(config: Config) -> AIAgent:
        async with semaphore:
            agent = AIAgent(config)
            await agent.initialize()
            return agent
    
    try:
        logger.info("Initializing batch AI Agent context", count=len(configs))
        
        # Initialize all agents concurrently
        agents = await asyncio.gather(*[
            init_agent(config) for config in configs
        ])
        
        yield agents
        
    except Exception as e:
        logger.error("Batch AI Agent context initialization failed", error=str(e))
        raise AIAgentError(f"Batch agent context initialization failed: {e}") from e
    finally:
        logger.info("Cleaning up batch AI Agent context")
        # Close all agents concurrently
        if agents:
            await asyncio.gather(*[
                agent.close() for agent in agents
            ], return_exceptions=True)  # Don't fail if some cleanup fails


class ManagedAIAgent:
    """
    Wrapper around AIAgent that ensures proper resource management.
    
    This class automatically handles initialization and cleanup, making it safe
    to use in long-running applications.
    """
    
    def __init__(self, config: Optional[Config] = None):
        self._config = config or load_config()
        self._agent: Optional['AIAgent'] = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _ensure_agent(self) -> 'AIAgent':
        """Ensure agent is initialized (thread-safe)."""
        if self._agent is None or not self._initialized:
            async with self._lock:
                if self._agent is None or not self._initialized:
                    from .agent import AIAgent
                    
                    if self._agent is not None:
                        await self._agent.close()
                    
                    self._agent = AIAgent(self._config)
                    await self._agent.initialize()
                    self._initialized = True
        
        return self._agent
    
    async def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process query with managed agent."""
        agent = await self._ensure_agent()
        return await agent.process_query(query, **kwargs)
    
    async def get_detailed_info(self, item_type: str, item_id: str) -> Dict[str, Any]:
        """Get detailed info with managed agent."""
        agent = await self._ensure_agent()
        return await agent.get_detailed_info(item_type, item_id)
    
    async def suggest_related_queries(self, query: str, context: Dict[str, Any]) -> List[str]:
        """Get query suggestions with managed agent."""
        agent = await self._ensure_agent()
        return await agent.suggest_related_queries(query, context)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on managed agent."""
        try:
            agent = await self._ensure_agent()
            # Simple test query to verify functionality
            test_response = await agent.process_query("test query")
            return {
                "status": "healthy",
                "initialized": self._initialized,
                "test_query_success": bool(test_response)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }
    
    async def close(self) -> None:
        """Close managed agent."""
        async with self._lock:
            if self._agent is not None:
                await self._agent.close()
                self._agent = None
                self._initialized = False


@asynccontextmanager 
async def managed_agent_pool(
    pool_size: int = 3,
    config: Optional[Config] = None
) -> AsyncGenerator[List[ManagedAIAgent], None]:
    """
    Create a pool of managed AI agents for high-throughput scenarios.
    
    Args:
        pool_size: Number of agents in the pool
        config: Configuration for all agents
        
    Yields:
        List of ManagedAIAgent instances
    """
    agents: List[ManagedAIAgent] = []
    
    try:
        logger.info("Creating managed agent pool", size=pool_size)
        
        # Create agent pool
        agents = [ManagedAIAgent(config) for _ in range(pool_size)]
        
        # Pre-warm the pool
        await asyncio.gather(*[
            agent._ensure_agent() for agent in agents
        ])
        
        yield agents
        
    except Exception as e:
        logger.error("Managed agent pool creation failed", error=str(e))
        raise AIAgentError(f"Agent pool creation failed: {e}") from e
    finally:
        logger.info("Cleaning up managed agent pool")
        if agents:
            await asyncio.gather(*[
                agent.close() for agent in agents
            ], return_exceptions=True)


class AgentResourceMonitor:
    """
    Monitor for AI Agent resource usage and health.
    
    Helps with debugging resource leaks and performance issues.
    """
    
    def __init__(self):
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.logger = structlog.get_logger("agent_monitor")
    
    def register_agent(self, agent_id: str, metadata: Dict[str, Any] = None) -> None:
        """Register a new agent for monitoring."""
        self.active_agents[agent_id] = {
            "created_at": asyncio.get_event_loop().time(),
            "metadata": metadata or {},
            "query_count": 0,
            "last_activity": None
        }
        self.logger.info("Agent registered", agent_id=agent_id)
    
    def record_query(self, agent_id: str) -> None:
        """Record a query execution for an agent."""
        if agent_id in self.active_agents:
            self.active_agents[agent_id]["query_count"] += 1
            self.active_agents[agent_id]["last_activity"] = asyncio.get_event_loop().time()
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.active_agents:
            agent_info = self.active_agents.pop(agent_id)
            self.logger.info(
                "Agent unregistered",
                agent_id=agent_id,
                lifetime=asyncio.get_event_loop().time() - agent_info["created_at"],
                query_count=agent_info["query_count"]
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        current_time = asyncio.get_event_loop().time()
        
        return {
            "active_agents": len(self.active_agents),
            "total_queries": sum(info["query_count"] for info in self.active_agents.values()),
            "agents": {
                agent_id: {
                    **info,
                    "age_seconds": current_time - info["created_at"],
                    "idle_seconds": (
                        current_time - info["last_activity"] 
                        if info["last_activity"] else None
                    )
                }
                for agent_id, info in self.active_agents.items()
            }
        }


# Global resource monitor instance
agent_monitor = AgentResourceMonitor()


# Convenience function for simple usage
async def process_query_simple(query: str, config: Optional[Config] = None) -> Dict[str, Any]:
    """
    Simple function to process a query with automatic resource management.
    
    Args:
        query: Query string to process
        config: Optional configuration
        
    Returns:
        Query response dictionary
        
    Raises:
        AIAgentError: If processing fails
    """
    async with ai_agent_context(config) as agent:
        return await agent.process_query(query)