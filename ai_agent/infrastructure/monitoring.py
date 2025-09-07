import asyncio
import json
import time
import psutil
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import structlog
from structlog.processors import JSONRenderer
import colorlog


@dataclass
class MetricData:
    """Data structure for custom metrics"""
    name: str
    value: float
    labels: Dict[str, str]
    timestamp: float
    metric_type: str  # counter, gauge, histogram


class LoggingManager:
    """Advanced logging configuration and management"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_level = config.get('log_level', 'INFO')
        self.log_format = config.get('log_format', 'json')
        self.log_file = config.get('log_file', 'agent.log')
        self.enable_structured_logging = config.get('enable_structured_logging', True)
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Configure structlog
        if self.enable_structured_logging:
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    JSONRenderer() if self.log_format == 'json' else structlog.dev.ConsoleRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
        
        # Setup standard logging
        formatter = self._get_formatter()
        
        # Console handler with colors
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s%(reset)s: %(message)s',
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        ))
        console_handler.setLevel(self.log_level)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel('DEBUG')  # Log everything to file
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel('DEBUG')
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        # Setup specific loggers
        self._setup_component_loggers()
    
    def _get_formatter(self) -> logging.Formatter:
        """Get appropriate formatter based on configuration"""
        if self.log_format == 'json':
            return logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
        else:
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def _setup_component_loggers(self):
        """Setup loggers for different components"""
        components = [
            'ai_client', 'mcp_client', 'code_reader', 'agent', 
            'cache_manager', 'reliability', 'monitoring'
        ]
        
        for component in components:
            logger = logging.getLogger(component)
            logger.setLevel(self.log_level)


class MetricsCollector:
    """Prometheus-compatible metrics collection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.registry = CollectorRegistry()
        self.custom_metrics: List[MetricData] = []
        
        # Core metrics
        self.request_count = Counter(
            'agent_requests_total',
            'Total number of requests processed',
            ['endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'agent_request_duration_seconds',
            'Request duration in seconds',
            ['endpoint'],
            registry=self.registry
        )
        
        self.cache_hits = Counter(
            'agent_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'agent_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        self.circuit_breaker_state = Gauge(
            'agent_circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=half-open, 2=open)',
            ['service'],
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'agent_active_connections',
            'Number of active connections',
            ['service'],
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            registry=self.registry
        )
    
    def record_request(self, endpoint: str, status: str, duration: float):
        """Record request metrics"""
        self.request_count.labels(endpoint=endpoint, status=status).inc()
        self.request_duration.labels(endpoint=endpoint).observe(duration)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        self.cache_misses.labels(cache_type=cache_type).inc()
    
    def update_circuit_breaker_state(self, service: str, state: str):
        """Update circuit breaker state metric"""
        state_mapping = {'closed': 0, 'half_open': 1, 'open': 2}
        self.circuit_breaker_state.labels(service=service).set(
            state_mapping.get(state, 0)
        )
    
    def update_active_connections(self, service: str, count: int):
        """Update active connections metric"""
        self.active_connections.labels(service=service).set(count)
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.system_cpu_usage.set(cpu_percent)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.system_memory_usage.set(memory.used)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        self.system_disk_usage.set(disk.used)
    
    def add_custom_metric(self, name: str, value: float, labels: Dict[str, str], 
                         metric_type: str = 'gauge'):
        """Add custom metric"""
        metric = MetricData(
            name=name,
            value=value,
            labels=labels,
            timestamp=time.time(),
            metric_type=metric_type
        )
        self.custom_metrics.append(metric)
        
        # Keep only recent metrics (last 1000)
        if len(self.custom_metrics) > 1000:
            self.custom_metrics = self.custom_metrics[-1000:]
    
    def get_metrics(self) -> str:
        """Get Prometheus-formatted metrics"""
        return generate_latest(self.registry).decode('utf-8')
    
    def get_custom_metrics(self) -> List[Dict[str, Any]]:
        """Get custom metrics as JSON"""
        return [asdict(metric) for metric in self.custom_metrics]


class PerformanceMonitor:
    """Monitor performance and generate alerts"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_collector = MetricsCollector(config)
        self.alerts: List[Dict[str, Any]] = []
        
        # Thresholds
        self.cpu_threshold = config.get('cpu_alert_threshold', 80.0)
        self.memory_threshold = config.get('memory_alert_threshold', 85.0)
        self.response_time_threshold = config.get('response_time_threshold', 5.0)
        self.error_rate_threshold = config.get('error_rate_threshold', 0.1)
        
        # Monitoring task
        self.monitoring_task = None
        self.logger = structlog.get_logger(__name__)
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                await self._collect_system_metrics()
                await self._check_alerts()
                await asyncio.sleep(self.config.get('monitoring_interval', 30))
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        self.metrics_collector.update_system_metrics()
        
        # Log system stats periodically
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.logger.debug(
            "System metrics",
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100
        )
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        current_time = time.time()
        
        # CPU alert
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > self.cpu_threshold:
            await self._create_alert(
                'high_cpu_usage',
                f'CPU usage is {cpu_percent:.1f}% (threshold: {self.cpu_threshold}%)',
                'warning'
            )
        
        # Memory alert
        memory = psutil.virtual_memory()
        if memory.percent > self.memory_threshold:
            await self._create_alert(
                'high_memory_usage',
                f'Memory usage is {memory.percent:.1f}% (threshold: {self.memory_threshold}%)',
                'warning'
            )
    
    async def _create_alert(self, alert_type: str, message: str, severity: str):
        """Create and store alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': time.time(),
            'resolved': False
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts (last 100)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        self.logger.warning(f"Alert created: {alert}")
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by resolved status"""
        if resolved is None:
            return self.alerts.copy()
        return [alert for alert in self.alerts if alert['resolved'] == resolved]
    
    def resolve_alert(self, alert_index: int):
        """Mark alert as resolved"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index]['resolved'] = True
            self.alerts[alert_index]['resolved_at'] = time.time()


class HealthChecker:
    """Health check functionality for services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.last_health_check = {}
    
    async def check_service_health(self, service_name: str, health_check_func) -> Dict[str, Any]:
        """Perform health check on a service"""
        start_time = time.time()
        health_status = {
            'service': service_name,
            'status': 'unknown',
            'timestamp': start_time,
            'response_time': 0,
            'details': {}
        }
        
        try:
            # Execute health check
            if asyncio.iscoroutinefunction(health_check_func):
                result = await asyncio.wait_for(health_check_func(), timeout=10)
            else:
                result = health_check_func()
            
            health_status['status'] = 'healthy'
            health_status['details'] = result if isinstance(result, dict) else {'result': str(result)}
            
        except asyncio.TimeoutError:
            health_status['status'] = 'timeout'
            health_status['details'] = {'error': 'Health check timed out'}
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['details'] = {'error': str(e)}
        
        health_status['response_time'] = time.time() - start_time
        self.last_health_check[service_name] = health_status
        
        return health_status
    
    async def check_all_services(self, services: Dict[str, callable]) -> Dict[str, Any]:
        """Check health of all services"""
        results = {}
        tasks = []
        
        for service_name, health_check_func in services.items():
            task = self.check_service_health(service_name, health_check_func)
            tasks.append((service_name, task))
        
        for service_name, task in tasks:
            try:
                results[service_name] = await task
            except Exception as e:
                results[service_name] = {
                    'service': service_name,
                    'status': 'error',
                    'timestamp': time.time(),
                    'details': {'error': str(e)}
                }
        
        return results
    
    def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get last health check result for a service"""
        return self.last_health_check.get(service_name)


# Global monitoring instances
monitoring_config = {
    'log_level': 'INFO',
    'log_format': 'json',
    'enable_structured_logging': True,
    'monitoring_interval': 30,
    'cpu_alert_threshold': 80.0,
    'memory_alert_threshold': 85.0
}

logging_manager = LoggingManager(monitoring_config)
performance_monitor = PerformanceMonitor(monitoring_config)
metrics_collector = MetricsCollector(monitoring_config)
health_checker = HealthChecker(monitoring_config)