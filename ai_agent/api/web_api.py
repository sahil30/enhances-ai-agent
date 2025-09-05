import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog

from ..core.agent import AIAgent
from ..core.config import load_config
from ..core.query_processor import query_processor, QueryAnalysis
from ..infrastructure.batch_processor import batch_processor, BatchResult
from ..infrastructure.semantic_search import semantic_search
from ..infrastructure.monitoring import performance_monitor, metrics_collector
from ..infrastructure.cache_manager import CacheManager
from ..plugins.plugin_system import plugin_manager, PluginContext, PluginEvent

logger = structlog.get_logger(__name__)

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    search_options: Optional[Dict[str, Any]] = Field(default=None, description="Search options")
    use_cache: bool = Field(default=True, description="Whether to use caching")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class BatchQueryRequest(BaseModel):
    queries: List[str] = Field(..., min_items=1, max_items=50, description="List of queries to process")
    search_options: Optional[Dict[str, Any]] = Field(default=None, description="Search options for all queries")
    callback_url: Optional[str] = Field(default=None, description="URL to call when batch is complete")


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    source_types: Optional[List[str]] = Field(default=None, description="Source types to search")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    min_score: float = Field(default=0.1, ge=0.0, le=1.0, description="Minimum relevance score")


class IndexBuildRequest(BaseModel):
    source_type: str = Field(..., description="Type of source to index")
    documents: List[Dict[str, Any]] = Field(..., description="Documents to index")
    rebuild: bool = Field(default=False, description="Whether to rebuild existing index")


class PluginActionRequest(BaseModel):
    plugin_name: str = Field(..., description="Name of the plugin")
    action: str = Field(..., description="Action to perform (enable/disable/reload)")


class QueryResponse(BaseModel):
    query: str
    solution: str
    sources: Dict[str, Any]
    processing_time: float
    cached: bool = False
    analysis: Optional[Dict[str, Any]] = None


class BatchResponse(BaseModel):
    batch_id: str
    status: str
    message: str


class APIResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# FastAPI app
app = FastAPI(
    title="AI Agent API",
    description="Advanced AI agent for searching Confluence, JIRA, and code repositories",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Authentication
security = HTTPBearer(auto_error=False)

# Global state
agent_instance: Optional[AIAgent] = None
cache_manager: Optional[CacheManager] = None


async def get_auth_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Extract and validate authentication token"""
    if not credentials:
        return None
    return credentials.credentials


async def startup_event():
    """Initialize services on startup"""
    global agent_instance, cache_manager
    
    logger.info("Starting AI Agent API server...")
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize cache manager
        cache_config = {
            'memory_cache_size': 1000,
            'memory_cache_ttl': 300,
            'use_redis': getattr(config, 'use_redis', False),
            'redis_host': getattr(config, 'redis_host', 'localhost'),
            'redis_port': getattr(config, 'redis_port', 6379),
            'file_cache_dir': './cache'
        }
        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize()
        
        # Initialize agent
        agent_instance = AIAgent(config)
        
        # Start batch processor
        await batch_processor.start_workers()
        
        # Start performance monitoring
        await performance_monitor.start_monitoring()
        
        # Load plugins
        await plugin_manager.load_plugins()
        
        logger.info("AI Agent API server started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_instance, cache_manager
    
    logger.info("Shutting down AI Agent API server...")
    
    try:
        if agent_instance:
            await agent_instance.close()
        
        if cache_manager:
            await cache_manager.close()
        
        await batch_processor.stop_workers()
        await performance_monitor.stop_monitoring()
        await plugin_manager.cleanup_all_plugins()
        
        logger.info("AI Agent API server shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Register startup/shutdown events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request received",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        processing_time=processing_time
    )
    
    # Record metrics
    metrics_collector.record_request(
        endpoint=request.url.path,
        status="success" if response.status_code < 400 else "error",
        duration=processing_time
    )
    
    return response


@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint"""
    return APIResponse(
        success=True,
        data={"message": "AI Agent API is running", "version": "2.0.0"},
        message="Welcome to AI Agent API"
    )


@app.post("/search", response_model=APIResponse)
async def search_query(request: QueryRequest, token: str = Depends(get_auth_token)):
    """Search for information across all sources"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    start_time = time.time()
    
    try:
        # Execute pre-query plugins
        context = PluginContext(
            query=request.query,
            config=request.search_options or {},
            metadata={"start_time": start_time}
        )
        context = await plugin_manager.execute_event_handlers(PluginEvent.PRE_QUERY, context)
        
        # Check cache if enabled
        cached_result = None
        if request.use_cache and cache_manager:
            cache_key = f"query:{request.query}:{hash(str(request.search_options))}"
            cached_result = await cache_manager.get(cache_key, 'ai_response')
        
        if cached_result:
            logger.info(f"Cache hit for query: {request.query}")
            metrics_collector.record_cache_hit('ai_response')
            
            response_data = cached_result
            response_data['cached'] = True
            response_data['processing_time'] = time.time() - start_time
        else:
            # Process query
            result = await agent_instance.process_query(request.query, request.search_options)
            
            # Analyze query
            analysis = query_processor.analyze_query(request.query)
            
            response_data = {
                'query': request.query,
                'solution': result.get('solution', ''),
                'sources': result.get('sources', {}),
                'processing_time': time.time() - start_time,
                'cached': False,
                'analysis': {
                    'query_type': analysis.query_type.value,
                    'intent': analysis.intent.value,
                    'keywords': analysis.keywords,
                    'technical_terms': analysis.technical_terms,
                    'confidence_score': analysis.confidence_score
                }
            }
            
            # Cache result
            if request.use_cache and cache_manager:
                await cache_manager.set(cache_key, response_data, 'ai_response')
                metrics_collector.record_cache_miss('ai_response')
        
        # Execute post-query plugins
        context.results = [response_data]
        context = await plugin_manager.execute_event_handlers(PluginEvent.POST_QUERY, context)
        
        return APIResponse(
            success=True,
            data=response_data,
            message="Query processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/search", response_model=APIResponse)
async def batch_search(request: BatchQueryRequest, background_tasks: BackgroundTasks):
    """Submit batch search queries"""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        batch_id = await batch_processor.process_queries_batch(
            queries=request.queries,
            agent_instance=agent_instance,
            search_options=request.search_options
        )
        
        return APIResponse(
            success=True,
            data={"batch_id": batch_id, "total_queries": len(request.queries)},
            message="Batch submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/{batch_id}/status", response_model=APIResponse)
async def get_batch_status(batch_id: str):
    """Get status of a batch operation"""
    try:
        status = await batch_processor.get_batch_status(batch_id)
        if not status:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return APIResponse(
            success=True,
            data=status,
            message="Batch status retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/batch/{batch_id}/results", response_model=APIResponse)
async def get_batch_results(batch_id: str):
    """Get results of a completed batch operation"""
    try:
        results = await batch_processor.get_batch_results(batch_id)
        if not results:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return APIResponse(
            success=True,
            data=results,
            message="Batch results retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/semantic/search", response_model=APIResponse)
async def semantic_search_endpoint(request: SemanticSearchRequest):
    """Perform semantic search"""
    try:
        results = await semantic_search.search(
            query=request.query,
            source_types=request.source_types,
            limit=request.limit,
            min_score=request.min_score
        )
        
        # Convert SearchResult objects to dicts
        results_data = []
        for result in results:
            results_data.append({
                'content': result.content,
                'source': result.source,
                'source_type': result.source_type,
                'title': result.title,
                'url': result.url,
                'relevance_score': result.combined_score,
                'semantic_score': result.semantic_score,
                'keyword_score': result.keyword_score,
                'metadata': result.metadata
            })
        
        return APIResponse(
            success=True,
            data={
                'query': request.query,
                'results': results_data,
                'total_results': len(results_data)
            },
            message="Semantic search completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/semantic/build-index", response_model=APIResponse)
async def build_semantic_index(request: IndexBuildRequest, background_tasks: BackgroundTasks):
    """Build semantic search index"""
    try:
        # Build index in background
        background_tasks.add_task(
            semantic_search.build_index,
            request.documents,
            request.source_type
        )
        
        return APIResponse(
            success=True,
            data={
                'source_type': request.source_type,
                'document_count': len(request.documents),
                'status': 'building'
            },
            message="Index build started"
        )
        
    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/semantic/stats", response_model=APIResponse)
async def get_semantic_stats():
    """Get semantic search statistics"""
    try:
        stats = semantic_search.get_index_stats()
        
        return APIResponse(
            success=True,
            data=stats,
            message="Semantic search statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting semantic stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/plugins", response_model=APIResponse)
async def list_plugins():
    """List all loaded plugins"""
    try:
        plugins = plugin_manager.get_plugin_status()
        
        return APIResponse(
            success=True,
            data=plugins,
            message="Plugins listed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error listing plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plugins/action", response_model=APIResponse)
async def plugin_action(request: PluginActionRequest):
    """Perform action on a plugin"""
    try:
        success = False
        
        if request.action == "enable":
            success = await plugin_manager.enable_plugin(request.plugin_name)
        elif request.action == "disable":
            success = await plugin_manager.disable_plugin(request.plugin_name)
        elif request.action == "reload":
            success = await plugin_manager.reload_plugin(request.plugin_name)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
        if success:
            return APIResponse(
                success=True,
                data={"plugin": request.plugin_name, "action": request.action},
                message=f"Plugin action {request.action} completed successfully"
            )
        else:
            raise HTTPException(status_code=404, detail="Plugin not found or action failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing plugin action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'agent': agent_instance is not None,
                'cache': cache_manager is not None,
                'batch_processor': batch_processor._workers_running,
                'plugins': len(plugin_manager.plugins)
            }
        }
        
        # Check service health
        if agent_instance:
            # Could add more specific health checks here
            pass
        
        return APIResponse(
            success=True,
            data=health_data,
            message="System is healthy"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return APIResponse(
            success=False,
            data={'status': 'unhealthy', 'error': str(e)},
            message="System health check failed"
        )


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics"""
    try:
        # Update system metrics
        metrics_collector.update_system_metrics()
        
        # Generate Prometheus format
        metrics_data = metrics_collector.get_metrics()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")


@app.get("/stats", response_model=APIResponse)
async def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        stats = {
            'batch_processor': batch_processor.get_system_stats(),
            'cache': await cache_manager.get_stats() if cache_manager else {},
            'plugins': len(plugin_manager.plugins),
            'semantic_search': semantic_search.get_index_stats()
        }
        
        return APIResponse(
            success=True,
            data=stats,
            message="System statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Run the FastAPI server"""
    uvicorn.run(
        "web_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Agent Web API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port, debug=args.debug)