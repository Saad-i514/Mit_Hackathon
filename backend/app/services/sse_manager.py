"""
Server-Sent Events (SSE) Stream Manager
Manages real-time progress streaming for experiment plan generation
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from sse_starlette.sse import ServerSentEvent


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """SSE event types"""
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETE = "complete"
    STAGE_START = "stage_start"
    STAGE_COMPLETE = "stage_complete"


class SSEEvent(BaseModel):
    """SSE event data structure"""
    event_type: EventType
    timestamp: str
    data: Dict[str, Any]
    
    def to_sse_event(self) -> ServerSentEvent:
        """Convert to sse_starlette ServerSentEvent."""
        payload = json.dumps(self.model_dump())
        return ServerSentEvent(data=payload, event=self.event_type.value)


class SSEManager:
    """
    Manages Server-Sent Events for real-time progress streaming
    
    Provides thread-safe event emission and consumption for pipeline progress,
    errors, and completion events during experiment plan generation.
    """
    
    def __init__(self, max_queue_size: int = 100):
        """
        Initialize SSE Manager
        
        Args:
            max_queue_size: Maximum number of events to queue
        """
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.is_active = True
        self._connection_count = 0
        
        logger.info(f"SSEManager initialized with max queue size: {max_queue_size}")
    
    async def emit_progress(
        self,
        stage: str,
        progress_percent: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Emit progress event
        
        Args:
            stage: Current pipeline stage (validation, literature_qc, plan_generation)
            progress_percent: Progress percentage (0-100)
            message: Human-readable progress message
            details: Optional additional details
        """
        event_data = {
            "stage": stage,
            "progress_percent": progress_percent,
            "message": message,
            "details": details or {}
        }
        
        await self._emit_event(EventType.PROGRESS, event_data)
        logger.debug(f"Progress event: {stage} - {progress_percent}% - {message}")
    
    async def emit_stage_start(
        self,
        stage: str,
        stage_description: str,
        estimated_duration: Optional[int] = None
    ):
        """
        Emit stage start event
        
        Args:
            stage: Pipeline stage name
            stage_description: Human-readable stage description
            estimated_duration: Estimated duration in seconds
        """
        event_data = {
            "stage": stage,
            "description": stage_description,
            "estimated_duration": estimated_duration
        }
        
        await self._emit_event(EventType.STAGE_START, event_data)
        logger.info(f"Stage started: {stage} - {stage_description}")
    
    async def emit_stage_complete(
        self,
        stage: str,
        duration: float,
        result_summary: Optional[Dict[str, Any]] = None
    ):
        """
        Emit stage completion event
        
        Args:
            stage: Pipeline stage name
            duration: Actual duration in seconds
            result_summary: Optional summary of stage results
        """
        event_data = {
            "stage": stage,
            "duration": duration,
            "result_summary": result_summary or {}
        }
        
        await self._emit_event(EventType.STAGE_COMPLETE, event_data)
        logger.info(f"Stage completed: {stage} - {duration:.2f}s")
    
    async def emit_error(
        self,
        error_code: str,
        error_message: str,
        stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Emit error event
        
        Args:
            error_code: Error code for client handling
            error_message: Human-readable error message
            stage: Stage where error occurred
            details: Optional error details
        """
        event_data = {
            "error_code": error_code,
            "message": error_message,
            "stage": stage,
            "details": details or {}
        }
        
        await self._emit_event(EventType.ERROR, event_data)
        logger.error(f"Error event: {error_code} - {error_message} (stage: {stage})")
    
    async def emit_complete(
        self,
        plan_id: str,
        total_duration: float,
        summary: Optional[Dict[str, Any]] = None
    ):
        """
        Emit completion event
        
        Args:
            plan_id: Generated experiment plan ID
            total_duration: Total pipeline duration in seconds
            summary: Optional pipeline execution summary
        """
        event_data = {
            "plan_id": plan_id,
            "total_duration": total_duration,
            "summary": summary or {}
        }
        
        await self._emit_event(EventType.COMPLETE, event_data)
        logger.info(f"Pipeline completed: plan_id={plan_id}, duration={total_duration:.2f}s")
        
        # Mark stream as inactive after completion
        self.is_active = False
    
    async def _emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """
        Internal method to emit event to queue
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if not self.is_active:
            logger.warning(f"Attempted to emit {event_type} event on inactive stream")
            return
        
        event = SSEEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            data=data
        )
        
        try:
            # Use put_nowait to avoid blocking if queue is full
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning(f"SSE event queue full, dropping {event_type} event")
    
    async def event_stream(self) -> AsyncGenerator[ServerSentEvent, None]:
        """
        Async generator for SSE event consumption.
        Yields ServerSentEvent objects consumed by sse_starlette EventSourceResponse.
        """
        self._connection_count += 1
        connection_id = self._connection_count
        
        logger.info(f"SSE stream started (connection {connection_id})")
        
        try:
            while self.is_active or not self.event_queue.empty():
                try:
                    # Wait for event with timeout to allow periodic checks
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                    
                    # Yield properly formatted ServerSentEvent
                    yield event.to_sse_event()
                    
                    # Mark task as done
                    self.event_queue.task_done()
                    
                    # If this was a completion event, break the loop
                    if event.event_type == EventType.COMPLETE:
                        break
                
                except asyncio.TimeoutError:
                    # Send keep-alive ping to prevent connection timeout
                    yield ServerSentEvent(comment="keep-alive")
                    continue
        
        except Exception as e:
            logger.error(f"SSE stream error (connection {connection_id}): {e}")
            error_event = SSEEvent(
                event_type=EventType.ERROR,
                timestamp=datetime.utcnow().isoformat(),
                data={
                    "error_code": "STREAM_ERROR",
                    "message": "Stream connection error",
                    "details": {"error": str(e)}
                }
            )
            yield error_event.to_sse_event()
        
        finally:
            logger.info(f"SSE stream ended (connection {connection_id})")
    
    def close(self):
        """
        Close the SSE manager and mark as inactive
        """
        self.is_active = False
        logger.info("SSEManager closed")
    
    @property
    def queue_size(self) -> int:
        """Get current queue size"""
        return self.event_queue.qsize()
    
    @property
    def connection_count(self) -> int:
        """Get total connection count"""
        return self._connection_count


def create_sse_manager(max_queue_size: int = 100) -> SSEManager:
    """
    Factory function to create SSEManager instance
    
    Args:
        max_queue_size: Maximum number of events to queue
    
    Returns:
        SSEManager: Configured SSE manager instance
    """
    return SSEManager(max_queue_size=max_queue_size)