import asyncio
import time
from typing import Any, Callable, Dict, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_sleep_log
)
import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: tuple = (Exception,)
    success_threshold: int = 3  # For half-open state


@dataclass
class CircuitBreakerStats:
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    state: CircuitState = CircuitState.CLOSED
    total_calls: int = 0
    failed_calls: int = 0


class CircuitBreaker:
    """Circuit breaker pattern implementation for fault tolerance"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            self.stats.total_calls += 1
            
            # Check circuit state
            if self.stats.state == CircuitState.OPEN:
                if time.time() - self.stats.last_failure_time > self.config.recovery_timeout:
                    self.stats.state = CircuitState.HALF_OPEN
                    self.stats.success_count = 0
                    logger.info(f"Circuit breaker {self.name} entering half-open state")
                else:
                    raise CircuitBreakerOpenException(f"Circuit breaker {self.name} is open")
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                await self._on_success()
                return result
            
            except self.config.expected_exception as e:
                await self._on_failure(e)
                raise
    
    async def _on_success(self):
        """Handle successful call"""
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.success_count += 1
            if self.stats.success_count >= self.config.success_threshold:
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0
                logger.info(f"Circuit breaker {self.name} reset to closed state")
        elif self.stats.state == CircuitState.CLOSED:
            self.stats.failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.stats.failed_calls += 1
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()
        
        if self.stats.failure_count >= self.config.failure_threshold:
            self.stats.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} opened due to {self.stats.failure_count} failures")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.stats.state.value,
            'failure_count': self.stats.failure_count,
            'success_count': self.stats.success_count,
            'total_calls': self.stats.total_calls,
            'failed_calls': self.stats.failed_calls,
            'failure_rate': self.stats.failed_calls / max(self.stats.total_calls, 1),
            'last_failure_time': self.stats.last_failure_time
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class ReliabilityManager:
    """Manages circuit breakers and retry policies for different services"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_configs = {
            'ai_api': {
                'stop': stop_after_attempt(3),
                'wait': wait_exponential(multiplier=1, min=1, max=10),
                'retry': retry_if_exception_type((ConnectionError, TimeoutError)),
                'before_sleep': before_sleep_log(logger, 'WARNING')
            },
            'confluence_mcp': {
                'stop': stop_after_attempt(5),
                'wait': wait_exponential(multiplier=1, min=2, max=30),
                'retry': retry_if_exception_type((ConnectionError, TimeoutError)),
                'before_sleep': before_sleep_log(logger, 'WARNING')
            },
            'jira_mcp': {
                'stop': stop_after_attempt(5),
                'wait': wait_exponential(multiplier=1, min=2, max=30),
                'retry': retry_if_exception_type((ConnectionError, TimeoutError)),
                'before_sleep': before_sleep_log(logger, 'WARNING')
            },
            'file_operations': {
                'stop': stop_after_attempt(2),
                'wait': wait_exponential(multiplier=0.5, min=0.5, max=5),
                'retry': retry_if_exception_type((IOError, OSError)),
                'before_sleep': before_sleep_log(logger, 'INFO')
            }
        }
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if name not in self.circuit_breakers:
            if config is None:
                # Default configurations for different services
                if 'ai_api' in name:
                    config = CircuitBreakerConfig(
                        failure_threshold=3,
                        recovery_timeout=30,
                        expected_exception=(ConnectionError, TimeoutError, Exception)
                    )
                elif 'mcp' in name:
                    config = CircuitBreakerConfig(
                        failure_threshold=5,
                        recovery_timeout=60,
                        expected_exception=(ConnectionError, TimeoutError)
                    )
                else:
                    config = CircuitBreakerConfig()
            
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        
        return self.circuit_breakers[name]
    
    def get_retry_decorator(self, service_name: str):
        """Get retry decorator for specific service"""
        config = self.retry_configs.get(service_name, self.retry_configs['ai_api'])
        return retry(**config)
    
    async def call_with_circuit_breaker(self, service_name: str, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection"""
        circuit_breaker = self.get_circuit_breaker(service_name)
        return await circuit_breaker.call(func, *args, **kwargs)
    
    def call_with_retry(self, service_name: str):
        """Decorator for retry functionality"""
        return self.get_retry_decorator(service_name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all monitored services"""
        health_status = {
            'overall_status': 'healthy',
            'services': {},
            'timestamp': time.time()
        }
        
        unhealthy_services = []
        
        for name, circuit_breaker in self.circuit_breakers.items():
            stats = circuit_breaker.get_stats()
            service_health = {
                'status': 'healthy' if stats['state'] != 'open' else 'unhealthy',
                'circuit_breaker_state': stats['state'],
                'failure_rate': stats['failure_rate'],
                'total_calls': stats['total_calls']
            }
            
            if service_health['status'] == 'unhealthy':
                unhealthy_services.append(name)
            
            health_status['services'][name] = service_health
        
        if unhealthy_services:
            health_status['overall_status'] = 'degraded'
            health_status['unhealthy_services'] = unhealthy_services
        
        return health_status


class BulkheadIsolation:
    """Bulkhead pattern for resource isolation"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_calls = 0
        self.total_calls = 0
        self.rejected_calls = 0
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead isolation"""
        if self.semaphore.locked():
            self.rejected_calls += 1
            raise BulkheadRejectedException("Resource pool exhausted")
        
        async with self.semaphore:
            self.active_calls += 1
            self.total_calls += 1
            try:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            finally:
                self.active_calls -= 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics"""
        return {
            'active_calls': self.active_calls,
            'total_calls': self.total_calls,
            'rejected_calls': self.rejected_calls,
            'available_resources': self.semaphore._value
        }


class BulkheadRejectedException(Exception):
    """Exception raised when bulkhead rejects call"""
    pass


class TimeoutManager:
    """Timeout management for different operations"""
    
    TIMEOUTS = {
        'ai_api_call': 30,
        'mcp_search': 15,
        'mcp_details': 10,
        'file_read': 5,
        'cache_operation': 2
    }
    
    @classmethod
    async def with_timeout(cls, operation_type: str, coro):
        """Execute coroutine with appropriate timeout"""
        timeout = cls.TIMEOUTS.get(operation_type, 30)
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation {operation_type} timed out after {timeout}s")


# Global reliability manager instance
reliability_manager = ReliabilityManager()