"""
Circuit Breaker Pattern Implementation
Provides graceful degradation for external service calls
"""
import asyncio
import time
import logging
from typing import Callable, Any, Optional, Dict
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 3          # Number of failures to open circuit
    recovery_timeout: float = 30.0      # Seconds to wait before trying again
    expected_exception: type = Exception # Exception type that counts as failure
    success_threshold: int = 1          # Successes needed to close from half-open


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0
    total_calls: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls
    
    Prevents cascading failures by failing fast when a service is down
    and allowing periodic retries to check if the service has recovered.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {config}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open or function fails
        """
        async with self._lock:
            self.stats.total_calls += 1
            
            # Check if circuit should transition from open to half-open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._on_success()
            return result
        
        except self.config.expected_exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """Handle successful function execution"""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            
            logger.debug(f"Circuit breaker '{self.name}' success: {self.stats.success_count}")
    
    async def _on_failure(self):
        """Handle failed function execution"""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            
            logger.warning(f"Circuit breaker '{self.name}' failure: {self.stats.failure_count}")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.stats.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _transition_to_open(self):
        """Transition circuit to OPEN state"""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.stats.state_changes += 1
            logger.warning(f"Circuit breaker '{self.name}' transitioned to OPEN")
    
    def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state"""
        if self.state != CircuitState.HALF_OPEN:
            self.state = CircuitState.HALF_OPEN
            self.stats.success_count = 0  # Reset success count for half-open test
            self.stats.state_changes += 1
            logger.info(f"Circuit breaker '{self.name}' transitioned to HALF_OPEN")
    
    def _transition_to_closed(self):
        """Transition circuit to CLOSED state"""
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.stats.failure_count = 0  # Reset failure count
            self.stats.state_changes += 1
            logger.info(f"Circuit breaker '{self.name}' transitioned to CLOSED")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
            },
            "stats": {
                "failure_count": self.stats.failure_count,
                "success_count": self.stats.success_count,
                "last_failure_time": self.stats.last_failure_time,
                "last_success_time": self.stats.last_success_time,
                "state_changes": self.stats.state_changes,
                "total_calls": self.stats.total_calls,
            }
        }


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self._breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self._breakers[name] = CircuitBreaker(name, config)
        
        return self._breakers[name]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {name: breaker.get_status() for name, breaker in self._breakers.items()}


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    failure_threshold: int = 3,
    recovery_timeout: float = 30.0,
    expected_exception: type = Exception,
    success_threshold: int = 1
):
    """
    Decorator for applying circuit breaker pattern to functions
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures to open circuit
        recovery_timeout: Seconds to wait before trying again
        expected_exception: Exception type that counts as failure
        success_threshold: Successes needed to close from half-open
    """
    def decorator(func: Callable):
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            success_threshold=success_threshold
        )
        
        breaker = circuit_manager.get_breaker(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


# Predefined circuit breakers for external services
def get_openai_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for OpenAI API calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        expected_exception=Exception,
        success_threshold=2
    )
    return circuit_manager.get_breaker("openai", config)


def get_semantic_scholar_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Semantic Scholar API calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        expected_exception=Exception,
        success_threshold=1
    )
    return circuit_manager.get_breaker("semantic_scholar", config)


def get_serper_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Serper API calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        expected_exception=Exception,
        success_threshold=1
    )
    return circuit_manager.get_breaker("serper", config)


def get_supabase_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for Supabase database calls"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=10.0,
        expected_exception=Exception,
        success_threshold=2
    )
    return circuit_manager.get_breaker("supabase", config)