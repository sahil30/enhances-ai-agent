import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
import structlog

logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class BatchTask:
    """Individual task in a batch operation"""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    created_at: float = 0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class BatchResult:
    """Result of batch processing operation"""
    batch_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    total_time: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class TaskQueue:
    """Priority-based task queue for batch processing"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue = asyncio.PriorityQueue(maxsize=max_size)
        self._task_registry: Dict[str, BatchTask] = {}
    
    async def put(self, task: BatchTask) -> bool:
        """Add task to queue"""
        try:
            # Use negative priority for correct sorting (higher priority first)
            priority_value = -task.priority.value
            await self._queue.put((priority_value, task.created_at, task))
            self._task_registry[task.id] = task
            logger.debug(f"Task {task.id} added to queue", priority=task.priority.value)
            return True
        except asyncio.QueueFull:
            logger.warning(f"Task queue full, cannot add task {task.id}")
            return False
    
    async def get(self) -> BatchTask:
        """Get next task from queue"""
        _, _, task = await self._queue.get()
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        return task
    
    def task_done(self):
        """Mark task as done"""
        self._queue.task_done()
    
    def get_task(self, task_id: str) -> Optional[BatchTask]:
        """Get task by ID"""
        return self._task_registry.get(task_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        total_tasks = len(self._task_registry)
        status_counts = {}
        
        for task in self._task_registry.values():
            status_counts[task.status.value] = status_counts.get(task.status.value, 0) + 1
        
        return {
            'queue_size': self._queue.qsize(),
            'total_tasks': total_tasks,
            'status_distribution': status_counts,
            'max_size': self.max_size
        }


class BatchProcessor:
    """High-performance batch processing system with concurrent execution"""
    
    def __init__(self, 
                 max_workers: int = 10,
                 max_concurrent_batches: int = 5,
                 default_timeout: float = 30.0):
        self.max_workers = max_workers
        self.max_concurrent_batches = max_concurrent_batches
        self.default_timeout = default_timeout
        
        self.task_queue = TaskQueue()
        self.worker_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.active_batches: Dict[str, Dict[str, Any]] = {}
        self.batch_semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        self._workers_running = False
        self._worker_tasks: List[asyncio.Task] = []
    
    async def start_workers(self):
        """Start background worker tasks"""
        if self._workers_running:
            return
        
        self._workers_running = True
        logger.info(f"Starting {self.max_workers} batch processing workers")
        
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(worker_task)
    
    async def stop_workers(self):
        """Stop background worker tasks"""
        if not self._workers_running:
            return
        
        self._workers_running = False
        logger.info("Stopping batch processing workers")
        
        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        
        # Shutdown thread pool
        self.worker_pool.shutdown(wait=True)
    
    async def submit_batch(self, 
                          tasks: List[Dict[str, Any]], 
                          batch_name: Optional[str] = None,
                          callback: Optional[Callable] = None) -> str:
        """Submit batch of tasks for processing"""
        batch_id = str(uuid.uuid4())
        batch_name = batch_name or f"batch-{batch_id[:8]}"
        
        logger.info(f"Submitting batch {batch_name} with {len(tasks)} tasks")
        
        # Create batch tasks
        batch_tasks = []
        for i, task_def in enumerate(tasks):
            task = BatchTask(
                id=f"{batch_id}-{i}",
                name=task_def.get('name', f'task-{i}'),
                func=task_def['func'],
                args=task_def.get('args', ()),
                kwargs=task_def.get('kwargs', {}),
                priority=TaskPriority(task_def.get('priority', TaskPriority.NORMAL.value)),
                timeout=task_def.get('timeout', self.default_timeout),
                max_retries=task_def.get('max_retries', 3)
            )
            batch_tasks.append(task)
        
        # Register batch
        self.active_batches[batch_id] = {
            'id': batch_id,
            'name': batch_name,
            'tasks': batch_tasks,
            'created_at': time.time(),
            'callback': callback,
            'status': 'submitted'
        }
        
        # Submit tasks to queue
        for task in batch_tasks:
            await self.task_queue.put(task)
        
        return batch_id
    
    async def process_queries_batch(self, 
                                  queries: List[str],
                                  agent_instance,
                                  search_options: Optional[Dict[str, Any]] = None) -> str:
        """Specialized batch processing for multiple queries"""
        tasks = []
        
        for i, query in enumerate(queries):
            task_def = {
                'name': f'query-{i}',
                'func': agent_instance.process_query,
                'args': (query,),
                'kwargs': {'search_options': search_options or {}},
                'priority': TaskPriority.NORMAL.value,
                'timeout': 60.0
            }
            tasks.append(task_def)
        
        return await self.submit_batch(tasks, f"query-batch-{len(queries)}")
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch operation"""
        batch = self.active_batches.get(batch_id)
        if not batch:
            return None
        
        tasks = batch['tasks']
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED])
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        
        return {
            'batch_id': batch_id,
            'name': batch['name'],
            'status': batch['status'],
            'total_tasks': total_tasks,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'progress_percentage': (completed / total_tasks * 100) if total_tasks > 0 else 0,
            'created_at': batch['created_at'],
            'task_statuses': {t.id: t.status.value for t in tasks}
        }
    
    async def get_batch_results(self, batch_id: str) -> Optional[BatchResult]:
        """Get complete results of a batch operation"""
        batch = self.active_batches.get(batch_id)
        if not batch:
            return None
        
        tasks = batch['tasks']
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]
        
        total_time = 0
        if tasks:
            start_time = min(t.created_at for t in tasks)
            end_time = max(t.completed_at or time.time() for t in tasks)
            total_time = end_time - start_time
        
        results = []
        for task in completed_tasks:
            results.append({
                'task_id': task.id,
                'task_name': task.name,
                'result': task.result,
                'execution_time': (task.completed_at or 0) - (task.started_at or 0)
            })
        
        errors = []
        for task in failed_tasks:
            errors.append({
                'task_id': task.id,
                'task_name': task.name,
                'error': task.error,
                'retry_count': task.retry_count
            })
        
        success_rate = len(completed_tasks) / len(tasks) * 100 if tasks else 0
        
        return BatchResult(
            batch_id=batch_id,
            total_tasks=len(tasks),
            completed_tasks=len(completed_tasks),
            failed_tasks=len(failed_tasks),
            success_rate=success_rate,
            total_time=total_time,
            results=results,
            errors=errors
        )
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch operation"""
        batch = self.active_batches.get(batch_id)
        if not batch:
            return False
        
        # Cancel pending tasks
        for task in batch['tasks']:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
        
        batch['status'] = 'cancelled'
        logger.info(f"Batch {batch_id} cancelled")
        return True
    
    async def _worker_loop(self, worker_name: str):
        """Main worker loop for processing tasks"""
        logger.info(f"Worker {worker_name} started")
        
        while self._workers_running:
            try:
                # Get next task from queue
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    self.task_queue.task_done()
                    continue
                
                logger.debug(f"Worker {worker_name} processing task {task.id}")
                
                # Execute task with timeout and retry logic
                await self._execute_task(task, worker_name)
                
                # Mark task as done in queue
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                # No tasks available, continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _execute_task(self, task: BatchTask, worker_name: str):
        """Execute individual task with error handling and retries"""
        max_attempts = task.max_retries + 1
        
        for attempt in range(max_attempts):
            try:
                # Execute task function
                if asyncio.iscoroutinefunction(task.func):
                    # Async function
                    if task.timeout:
                        result = await asyncio.wait_for(
                            task.func(*task.args, **task.kwargs),
                            timeout=task.timeout
                        )
                    else:
                        result = await task.func(*task.args, **task.kwargs)
                else:
                    # Sync function - run in thread pool
                    result = await asyncio.get_event_loop().run_in_executor(
                        self.worker_pool,
                        task.func,
                        *task.args
                    )
                
                # Task completed successfully
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                
                logger.debug(f"Task {task.id} completed successfully by {worker_name}")
                
                # Execute callback if batch is complete
                await self._check_batch_completion(task.id)
                break
                
            except Exception as e:
                task.retry_count = attempt
                error_msg = f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}"
                
                if attempt < max_attempts - 1:
                    # Retry
                    logger.warning(f"Task {task.id} failed, retrying: {error_msg}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    # All attempts failed
                    task.status = TaskStatus.FAILED
                    task.error = error_msg
                    task.completed_at = time.time()
                    
                    logger.error(f"Task {task.id} failed permanently: {error_msg}")
                    
                    # Execute callback if batch is complete
                    await self._check_batch_completion(task.id)
    
    async def _check_batch_completion(self, task_id: str):
        """Check if batch is complete and execute callback if needed"""
        # Find which batch this task belongs to
        batch_id = task_id.split('-')[0]
        batch = self.active_batches.get(batch_id)
        
        if not batch:
            return
        
        # Check if all tasks in batch are complete
        all_complete = all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            for t in batch['tasks']
        )
        
        if all_complete and batch['status'] != 'completed':
            batch['status'] = 'completed'
            logger.info(f"Batch {batch_id} ({batch['name']}) completed")
            
            # Execute callback if provided
            if batch['callback']:
                try:
                    results = await self.get_batch_results(batch_id)
                    if asyncio.iscoroutinefunction(batch['callback']):
                        await batch['callback'](results)
                    else:
                        batch['callback'](results)
                except Exception as e:
                    logger.error(f"Batch callback error: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        queue_stats = self.task_queue.get_stats()
        
        active_batches = len([b for b in self.active_batches.values() if b['status'] != 'completed'])
        
        return {
            'workers': {
                'total_workers': self.max_workers,
                'active_workers': len([t for t in self._worker_tasks if not t.done()]),
                'max_concurrent_batches': self.max_concurrent_batches
            },
            'queue': queue_stats,
            'batches': {
                'total_batches': len(self.active_batches),
                'active_batches': active_batches,
                'completed_batches': len(self.active_batches) - active_batches
            },
            'thread_pool': {
                'max_workers': self.worker_pool._max_workers,
                'active_threads': len(self.worker_pool._threads)
            }
        }


# Global batch processor instance
batch_processor = BatchProcessor()