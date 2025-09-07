import asyncio
import time
import socket
import psutil
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import structlog
from ..core.config import Config, load_config

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = None
    timestamp: float = 0
    response_time_ms: float = 0
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()
        if self.details is None:
            self.details = {}


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    available_memory_gb: float
    available_disk_gb: float
    load_average: List[float]
    process_count: int
    network_connections: int


class ConfigurationValidator:
    """Validates system configuration and environment"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.required_env_vars = [
            'CUSTOM_AI_API_URL',
            'CUSTOM_AI_API_KEY',
            'CONFLUENCE_ACCESS_TOKEN',
            'JIRA_ACCESS_TOKEN'
        ]
    
    async def validate_all(self) -> List[HealthCheckResult]:
        """Run all configuration validations"""
        results = []
        
        # Validate environment variables
        results.append(await self._check_environment_variables())
        
        # Validate configuration values
        results.append(await self._check_configuration_values())
        
        # Validate file system access
        results.append(await self._check_file_system_access())
        
        # Validate network connectivity
        results.append(await self._check_network_connectivity())
        
        # Validate dependencies
        results.append(await self._check_dependencies())
        
        return results
    
    async def _check_environment_variables(self) -> HealthCheckResult:
        """Check required environment variables"""
        start_time = time.time()
        missing_vars = []
        
        try:
            for var in self.required_env_vars:
                value = getattr(self.config, var.lower(), None)
                if not value:
                    missing_vars.append(var)
            
            if missing_vars:
                return HealthCheckResult(
                    name="environment_variables",
                    status=HealthStatus.CRITICAL,
                    message=f"Missing required environment variables: {', '.join(missing_vars)}",
                    details={"missing_variables": missing_vars},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                name="environment_variables",
                status=HealthStatus.HEALTHY,
                message="All required environment variables are set",
                details={"checked_variables": self.required_env_vars},
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="environment_variables",
                status=HealthStatus.CRITICAL,
                message=f"Error checking environment variables: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_configuration_values(self) -> HealthCheckResult:
        """Validate configuration value formats and ranges"""
        start_time = time.time()
        issues = []
        
        try:
            # Check URL formats
            if not self._is_valid_url(self.config.custom_ai_api_url):
                issues.append("Invalid custom AI API URL format")
            
            if not self._is_valid_url(self.config.confluence_base_url):
                issues.append("Invalid Confluence base URL format")
            
            if not self._is_valid_url(self.config.jira_base_url):
                issues.append("Invalid JIRA base URL format")
            
            # Check WebSocket URLs
            if not self._is_valid_websocket_url(self.config.confluence_mcp_server_url):
                issues.append("Invalid Confluence MCP server URL format")
            
            if not self._is_valid_websocket_url(self.config.jira_mcp_server_url):
                issues.append("Invalid JIRA MCP server URL format")
            
            # Check path accessibility
            code_path = Path(self.config.code_repo_path)
            if not code_path.exists():
                issues.append(f"Code repository path does not exist: {code_path}")
            elif not code_path.is_dir():
                issues.append(f"Code repository path is not a directory: {code_path}")
            
            if issues:
                return HealthCheckResult(
                    name="configuration_values",
                    status=HealthStatus.WARNING,
                    message=f"Configuration issues found: {'; '.join(issues)}",
                    details={"issues": issues},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                name="configuration_values",
                status=HealthStatus.HEALTHY,
                message="All configuration values are valid",
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="configuration_values",
                status=HealthStatus.CRITICAL,
                message=f"Error validating configuration: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_file_system_access(self) -> HealthCheckResult:
        """Check file system permissions and space"""
        start_time = time.time()
        issues = []
        
        try:
            # Check code repository access
            code_path = Path(self.config.code_repo_path)
            if code_path.exists():
                if not os.access(code_path, os.R_OK):
                    issues.append(f"No read access to code repository: {code_path}")
            
            # Check cache directory access
            cache_dir = Path("./cache")
            cache_dir.mkdir(exist_ok=True)
            
            if not os.access(cache_dir, os.W_OK):
                issues.append(f"No write access to cache directory: {cache_dir}")
            
            # Check log file access
            log_dir = Path("./logs")
            log_dir.mkdir(exist_ok=True)
            
            if not os.access(log_dir, os.W_OK):
                issues.append(f"No write access to log directory: {log_dir}")
            
            # Check disk space
            disk_usage = psutil.disk_usage('.')
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 1:  # Less than 1GB free
                issues.append(f"Low disk space: {free_gb:.2f}GB available")
            
            if issues:
                status = HealthStatus.WARNING if free_gb > 0.1 else HealthStatus.CRITICAL
                return HealthCheckResult(
                    name="file_system_access",
                    status=status,
                    message=f"File system issues: {'; '.join(issues)}",
                    details={"issues": issues, "free_space_gb": free_gb},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                name="file_system_access",
                status=HealthStatus.HEALTHY,
                message=f"File system access OK, {free_gb:.2f}GB available",
                details={"free_space_gb": free_gb},
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="file_system_access",
                status=HealthStatus.CRITICAL,
                message=f"Error checking file system access: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_network_connectivity(self) -> HealthCheckResult:
        """Check network connectivity to external services"""
        start_time = time.time()
        connectivity_results = {}
        
        try:
            # Test AI API connectivity
            ai_host = self._extract_host(self.config.custom_ai_api_url)
            if ai_host:
                connectivity_results['ai_api'] = await self._test_tcp_connection(ai_host, 443)
            
            # Test Confluence connectivity
            confluence_host = self._extract_host(self.config.confluence_base_url)
            if confluence_host:
                connectivity_results['confluence'] = await self._test_tcp_connection(confluence_host, 443)
            
            # Test JIRA connectivity
            jira_host = self._extract_host(self.config.jira_base_url)
            if jira_host:
                connectivity_results['jira'] = await self._test_tcp_connection(jira_host, 443)
            
            # Test MCP server connectivity
            confluence_mcp_host = self._extract_host(self.config.confluence_mcp_server_url, default_port=3001)
            if confluence_mcp_host:
                connectivity_results['confluence_mcp'] = await self._test_tcp_connection(
                    confluence_mcp_host['host'], confluence_mcp_host['port']
                )
            
            jira_mcp_host = self._extract_host(self.config.jira_mcp_server_url, default_port=3002)
            if jira_mcp_host:
                connectivity_results['jira_mcp'] = await self._test_tcp_connection(
                    jira_mcp_host['host'], jira_mcp_host['port']
                )
            
            # Evaluate results
            failed_connections = [name for name, result in connectivity_results.items() if not result]
            
            if failed_connections:
                status = HealthStatus.WARNING if len(failed_connections) < len(connectivity_results) else HealthStatus.CRITICAL
                return HealthCheckResult(
                    name="network_connectivity",
                    status=status,
                    message=f"Failed connections: {', '.join(failed_connections)}",
                    details={"connectivity_results": connectivity_results},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.HEALTHY,
                message="All network connections successful",
                details={"connectivity_results": connectivity_results},
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="network_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Error checking network connectivity: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_dependencies(self) -> HealthCheckResult:
        """Check required Python dependencies"""
        start_time = time.time()
        missing_deps = []
        version_issues = []
        
        try:
            required_packages = [
                ('requests', '2.31.0'),
                ('fastapi', '0.104.0'),
                ('pydantic', '2.5.0'),
                ('httpx', '0.25.0'),
                ('websockets', '12.0.0'),
                ('click', '8.1.0'),
                ('structlog', '23.1.0'),
                ('prometheus_client', '0.18.0'),
                ('psutil', '5.9.0')
            ]
            
            for package_name, min_version in required_packages:
                try:
                    __import__(package_name)
                    # Note: Version checking would require packaging module
                    # For now, just check import success
                except ImportError:
                    missing_deps.append(package_name)
            
            if missing_deps:
                return HealthCheckResult(
                    name="dependencies",
                    status=HealthStatus.CRITICAL,
                    message=f"Missing required packages: {', '.join(missing_deps)}",
                    details={"missing_packages": missing_deps},
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            return HealthCheckResult(
                name="dependencies",
                status=HealthStatus.HEALTHY,
                message="All required dependencies are available",
                details={"checked_packages": [pkg for pkg, _ in required_packages]},
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="dependencies",
                status=HealthStatus.CRITICAL,
                message=f"Error checking dependencies: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL format is valid"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _is_valid_websocket_url(self, url: str) -> bool:
        """Check if WebSocket URL format is valid"""
        import re
        ws_pattern = re.compile(
            r'^wss?://'  # ws:// or wss://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return ws_pattern.match(url) is not None
    
    def _extract_host(self, url: str, default_port: int = 443) -> Optional[Dict[str, Any]]:
        """Extract hostname from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.hostname:
                return {
                    'host': parsed.hostname,
                    'port': parsed.port or default_port
                }
        except Exception:
            pass
        return None
    
    async def _test_tcp_connection(self, host: str, port: int, timeout: float = 5.0) -> bool:
        """Test TCP connection to host:port"""
        try:
            future = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(future, timeout=timeout)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False


class SystemHealthMonitor:
    """Monitor system health and resources"""
    
    def __init__(self):
        self.thresholds = {
            'cpu_critical': 90.0,
            'cpu_warning': 80.0,
            'memory_critical': 95.0,
            'memory_warning': 85.0,
            'disk_critical': 95.0,
            'disk_warning': 90.0
        }
    
    async def check_system_resources(self) -> HealthCheckResult:
        """Check system resource utilization"""
        start_time = time.time()
        
        try:
            metrics = self._get_system_metrics()
            issues = []
            status = HealthStatus.HEALTHY
            
            # Check CPU usage
            if metrics.cpu_percent >= self.thresholds['cpu_critical']:
                issues.append(f"Critical CPU usage: {metrics.cpu_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
                issues.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
                status = HealthStatus.WARNING
            
            # Check memory usage
            if metrics.memory_percent >= self.thresholds['memory_critical']:
                issues.append(f"Critical memory usage: {metrics.memory_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif metrics.memory_percent >= self.thresholds['memory_warning']:
                issues.append(f"High memory usage: {metrics.memory_percent:.1f}%")
                if status != HealthStatus.CRITICAL:
                    status = HealthStatus.WARNING
            
            # Check disk usage
            if metrics.disk_percent >= self.thresholds['disk_critical']:
                issues.append(f"Critical disk usage: {metrics.disk_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif metrics.disk_percent >= self.thresholds['disk_warning']:
                issues.append(f"High disk usage: {metrics.disk_percent:.1f}%")
                if status != HealthStatus.CRITICAL:
                    status = HealthStatus.WARNING
            
            message = "; ".join(issues) if issues else "System resources within normal ranges"
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                details=asdict(metrics),
                response_time_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"Error checking system resources: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Load average (Unix systems only)
        try:
            load_avg = list(psutil.getloadavg())
        except (AttributeError, OSError):
            load_avg = [0.0, 0.0, 0.0]  # Windows fallback
        
        # Process count
        process_count = len(psutil.pids())
        
        # Network connections
        try:
            network_connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            network_connections = 0
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100,
            available_memory_gb=memory.available / (1024**3),
            available_disk_gb=disk.free / (1024**3),
            load_average=load_avg,
            process_count=process_count,
            network_connections=network_connections
        )


class HealthCheckManager:
    """Centralized health check management"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.config_validator = ConfigurationValidator(self.config)
        self.system_monitor = SystemHealthMonitor()
        self.custom_checks: Dict[str, Callable] = {}
    
    def add_custom_check(self, name: str, check_func: Callable) -> None:
        """Add custom health check function"""
        self.custom_checks[name] = check_func
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive report"""
        start_time = time.time()
        
        # Run all checks concurrently
        tasks = []
        
        # Configuration checks
        config_task = asyncio.create_task(self.config_validator.validate_all())
        tasks.append(('configuration', config_task))
        
        # System resource check
        system_task = asyncio.create_task(self.system_monitor.check_system_resources())
        tasks.append(('system', system_task))
        
        # Custom checks
        for name, check_func in self.custom_checks.items():
            if asyncio.iscoroutinefunction(check_func):
                custom_task = asyncio.create_task(check_func())
            else:
                custom_task = asyncio.create_task(asyncio.to_thread(check_func))
            tasks.append((name, custom_task))
        
        # Collect results
        all_results = []
        
        for name, task in tasks:
            try:
                result = await task
                if isinstance(result, list):
                    all_results.extend(result)
                else:
                    all_results.append(result)
            except Exception as e:
                logger.error(f"Health check {name} failed: {e}")
                all_results.append(HealthCheckResult(
                    name=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}"
                ))
        
        # Determine overall status
        overall_status = self._determine_overall_status(all_results)
        
        return {
            'overall_status': overall_status.value,
            'timestamp': time.time(),
            'total_checks': len(all_results),
            'check_duration_ms': (time.time() - start_time) * 1000,
            'checks': [asdict(result) for result in all_results],
            'summary': self._generate_summary(all_results)
        }
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """Determine overall system health status"""
        if any(r.status == HealthStatus.CRITICAL for r in results):
            return HealthStatus.CRITICAL
        elif any(r.status == HealthStatus.WARNING for r in results):
            return HealthStatus.WARNING
        elif any(r.status == HealthStatus.UNKNOWN for r in results):
            return HealthStatus.UNKNOWN
        else:
            return HealthStatus.HEALTHY
    
    def _generate_summary(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate summary statistics"""
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = sum(1 for r in results if r.status == status)
        
        avg_response_time = sum(r.response_time_ms for r in results) / len(results) if results else 0
        
        return {
            'status_distribution': status_counts,
            'average_response_time_ms': avg_response_time,
            'critical_issues': [r.message for r in results if r.status == HealthStatus.CRITICAL],
            'warnings': [r.message for r in results if r.status == HealthStatus.WARNING]
        }


# Global health check manager
health_check_manager = HealthCheckManager()