import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from functools import wraps
import traceback
import sys
from app.core.config import settings
from app.utils.redis_utils import redis_cache
import time

class CustomJSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
            
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        if hasattr(record, "extra_data"):
            log_data["extra_data"] = record.extra_data
            
        return json.dumps(log_data)

class LoggerService:
    def __init__(self):
        self.logger = logging.getLogger("lifesync")
        self.logger.setLevel(settings.LOG_LEVEL)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomJSONFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler for errors
        error_handler = logging.FileHandler("errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(CustomJSONFormatter())
        self.logger.addHandler(error_handler)
        
        # Performance metrics
        self.performance_data = {}

    async def log_error(
        self,
        error: Exception,
        module: str,
        function: str,
        request_id: Optional[str] = None,
        user_id: Optional[int] = None,
        extra_data: Optional[Dict] = None
    ):
        """Log error with context"""
        self.logger.error(
            str(error),
            exc_info=True,
            extra={
                "module": module,
                "function": function,
                "request_id": request_id,
                "user_id": user_id,
                "extra_data": extra_data
            }
        )
        
        # Cache error for real-time monitoring
        error_key = f"error:{datetime.utcnow().timestamp()}"
        await redis_cache.set_json(error_key, {
            "error": str(error),
            "module": module,
            "function": function,
            "traceback": traceback.format_exc(),
            "request_id": request_id,
            "user_id": user_id,
            "extra_data": extra_data
        })

    def monitor_performance(self, module: str, function: str):
        """Decorator to monitor function performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Update performance metrics
                    metric_key = f"{module}.{function}"
                    if metric_key not in self.performance_data:
                        self.performance_data[metric_key] = {
                            "total_calls": 0,
                            "total_time": 0,
                            "avg_time": 0,
                            "min_time": float('inf'),
                            "max_time": 0
                        }
                    
                    metrics = self.performance_data[metric_key]
                    metrics["total_calls"] += 1
                    metrics["total_time"] += execution_time
                    metrics["avg_time"] = metrics["total_time"] / metrics["total_calls"]
                    metrics["min_time"] = min(metrics["min_time"], execution_time)
                    metrics["max_time"] = max(metrics["max_time"], execution_time)
                    
                    # Log slow executions
                    if execution_time > 1.0:  # More than 1 second
                        self.logger.warning(
                            f"Slow execution detected in {module}.{function}",
                            extra={
                                "execution_time": execution_time,
                                "module": module,
                                "function": function
                            }
                        )
                    
                    return result
                    
                except Exception as e:
                    await self.log_error(e, module, function)
                    raise
                    
            return wrapper
        return decorator

    async def get_performance_metrics(self, module: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for specified module or all modules"""
        if module:
            return {
                key: value for key, value in self.performance_data.items()
                if key.startswith(module)
            }
        return self.performance_data

    async def get_error_stats(self, time_range: str = "24h") -> Dict[str, Any]:
        """Get error statistics for the specified time range"""
        now = datetime.utcnow()
        
        if time_range == "24h":
            start_time = now - timedelta(hours=24)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        else:
            start_time = now - timedelta(hours=24)
        
        # Get errors from Redis
        error_pattern = "error:*"
        errors = []
        
        async for key in redis_cache.redis_client.scan_iter(match=error_pattern):
            error_data = await redis_cache.get_json(key)
            if error_data:
                timestamp = datetime.fromtimestamp(float(key.split(":")[1]))
                if timestamp >= start_time:
                    errors.append(error_data)
        
        # Calculate statistics
        error_stats = {
            "total_errors": len(errors),
            "errors_by_module": {},
            "most_common_errors": {},
            "error_trend": self._calculate_error_trend(errors)
        }
        
        # Group by module
        for error in errors:
            module = error.get("module", "unknown")
            if module not in error_stats["errors_by_module"]:
                error_stats["errors_by_module"][module] = 0
            error_stats["errors_by_module"][module] += 1
            
            # Track error types
            error_type = error.get("error", "unknown")
            if error_type not in error_stats["most_common_errors"]:
                error_stats["most_common_errors"][error_type] = 0
            error_stats["most_common_errors"][error_type] += 1
        
        return error_stats

    def _calculate_error_trend(self, errors: List[Dict]) -> Dict[str, int]:
        """Calculate error trend by hour"""
        trend = {}
        for error in errors:
            timestamp = datetime.fromtimestamp(float(error["timestamp"]))
            hour = timestamp.strftime("%Y-%m-%d %H:00")
            if hour not in trend:
                trend[hour] = 0
            trend[hour] += 1
        return trend

# Create global logger instance
logger = LoggerService()