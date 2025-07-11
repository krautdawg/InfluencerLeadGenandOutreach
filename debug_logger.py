"""
Robust Debug Logging System for Production Deployment
Tracks API calls, success/failure status, and detailed error information
"""
import logging
import json
import time
import functools
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import os
import httpx
from dataclasses import dataclass, asdict


@dataclass
class APICallMetrics:
    """Data class to store API call metrics"""
    api_name: str
    endpoint: str
    method: str
    start_time: float
    end_time: float = 0
    duration_ms: float = 0
    status_code: Optional[int] = None
    success: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    request_size: int = 0
    response_size: int = 0
    retry_count: int = 0
    session_id: Optional[str] = None


class DebugLogger:
    """Enhanced logging class for comprehensive API monitoring"""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.setup_logger()
        self.api_metrics: Dict[str, APICallMetrics] = {}
        
    def setup_logger(self):
        """Setup structured logging with JSON formatter for production"""
        # Don't add handlers if they already exist
        if self.logger.handlers:
            return
            
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create file handler for production logs
        file_handler = logging.FileHandler('api_debug.log')
        file_handler.setLevel(logging.DEBUG)
        
        # JSON formatter for structured logging
        json_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": %(message)s}'
        )
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(json_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def log_api_call_start(self, api_name: str, endpoint: str, method: str = "POST", 
                          request_data: Dict = None, session_id: str = None) -> str:
        """Log the start of an API call and return a call_id for tracking"""
        call_id = f"{api_name}_{int(time.time() * 1000)}"
        
        # Store metrics
        self.api_metrics[call_id] = APICallMetrics(
            api_name=api_name,
            endpoint=endpoint,
            method=method,
            start_time=time.time(),
            session_id=session_id,
            request_size=len(json.dumps(request_data or {}))
        )
        
        # Sanitize request data for logging (remove sensitive info)
        sanitized_request = self._sanitize_data(request_data or {})
        
        log_data = {
            "event": "api_call_start",
            "call_id": call_id,
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
            "request_size_bytes": self.api_metrics[call_id].request_size,
            "request_data": sanitized_request,
            "session_id": session_id[:8] + "..." if session_id else None
        }
        
        self.logger.info(json.dumps(log_data))
        return call_id
    
    def log_api_call_success(self, call_id: str, response_data: Dict = None, 
                           status_code: int = 200, response_size: int = 0):
        """Log successful API call completion"""
        if call_id not in self.api_metrics:
            self.logger.warning(f"Call ID {call_id} not found in metrics")
            return
        
        metrics = self.api_metrics[call_id]
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.success = True
        metrics.status_code = status_code
        metrics.response_size = response_size or len(json.dumps(response_data or {}))
        
        # Sanitize response data
        sanitized_response = self._sanitize_data(response_data or {})
        
        log_data = {
            "event": "api_call_success",
            "call_id": call_id,
            "api_name": metrics.api_name,
            "endpoint": metrics.endpoint,
            "duration_ms": round(metrics.duration_ms, 2),
            "status_code": status_code,
            "response_size_bytes": metrics.response_size,
            "response_data": sanitized_response,
            "performance": self._get_performance_category(metrics.duration_ms)
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_api_call_failure(self, call_id: str, error: Exception, status_code: int = None,
                           retry_count: int = 0, response_text: str = ""):
        """Log failed API call with detailed error information"""
        if call_id not in self.api_metrics:
            self.logger.warning(f"Call ID {call_id} not found in metrics")
            return
        
        metrics = self.api_metrics[call_id]
        metrics.end_time = time.time()
        metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
        metrics.success = False
        metrics.status_code = status_code
        metrics.error_type = type(error).__name__
        metrics.error_message = str(error)
        metrics.retry_count = retry_count
        
        # Categorize error type
        error_category = self._categorize_error(error, status_code)
        
        log_data = {
            "event": "api_call_failure",
            "call_id": call_id,
            "api_name": metrics.api_name,
            "endpoint": metrics.endpoint,
            "duration_ms": round(metrics.duration_ms, 2),
            "error_type": metrics.error_type,
            "error_message": metrics.error_message,
            "error_category": error_category,
            "status_code": status_code,
            "retry_count": retry_count,
            "response_text": response_text[:500] if response_text else "",  # Limit size
            "traceback": traceback.format_exc(),
            "recovery_suggestion": self._get_recovery_suggestion(error_category)
        }
        
        self.logger.error(json.dumps(log_data))
    
    def log_business_logic_error(self, operation: str, error_details: Dict, 
                               severity: str = "ERROR"):
        """Log business logic errors (non-API related)"""
        log_data = {
            "event": "business_logic_error",
            "operation": operation,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "error_details": error_details,
            "traceback": traceback.format_exc()
        }
        
        if severity == "ERROR":
            self.logger.error(json.dumps(log_data))
        elif severity == "WARNING":
            self.logger.warning(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))
    
    def log_performance_metrics(self, operation: str, duration_ms: float, 
                              additional_metrics: Dict = None):
        """Log performance metrics for operations"""
        log_data = {
            "event": "performance_metrics",
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "performance_category": self._get_performance_category(duration_ms),
            "timestamp": datetime.utcnow().isoformat(),
            "additional_metrics": additional_metrics or {}
        }
        
        self.logger.info(json.dumps(log_data))
    
    def get_api_summary(self, time_window_minutes: int = 60) -> Dict:
        """Get summary of API calls in the specified time window"""
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        recent_calls = [
            metrics for metrics in self.api_metrics.values()
            if metrics.start_time > cutoff_time
        ]
        
        if not recent_calls:
            return {"message": "No API calls in the specified time window"}
        
        success_count = sum(1 for call in recent_calls if call.success)
        failure_count = len(recent_calls) - success_count
        avg_duration = sum(call.duration_ms for call in recent_calls) / len(recent_calls)
        
        error_types = {}
        for call in recent_calls:
            if not call.success and call.error_type:
                error_types[call.error_type] = error_types.get(call.error_type, 0) + 1
        
        api_breakdown = {}
        for call in recent_calls:
            api_name = call.api_name
            if api_name not in api_breakdown:
                api_breakdown[api_name] = {"success": 0, "failure": 0, "avg_duration": 0}
            
            if call.success:
                api_breakdown[api_name]["success"] += 1
            else:
                api_breakdown[api_name]["failure"] += 1
        
        return {
            "time_window_minutes": time_window_minutes,
            "total_calls": len(recent_calls),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round((success_count / len(recent_calls)) * 100, 2),
            "average_duration_ms": round(avg_duration, 2),
            "error_types": error_types,
            "api_breakdown": api_breakdown
        }
    
    def _sanitize_data(self, data: Dict) -> Dict:
        """Remove sensitive information from data before logging"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = [
            'password', 'token', 'api_key', 'secret', 'sessionid', 
            'authorization', 'bearer', 'credential', 'key'
        ]
        
        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = f"[REDACTED_{len(str(value))}]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                sanitized[key] = [self._sanitize_data(item) for item in value[:3]]  # Limit array size
            else:
                # Limit string length for large content
                if isinstance(value, str) and len(value) > 200:
                    sanitized[key] = value[:200] + "..."
                else:
                    sanitized[key] = value
        
        return sanitized
    
    def _categorize_error(self, error: Exception, status_code: int = None) -> str:
        """Categorize error type for better troubleshooting"""
        if isinstance(error, httpx.TimeoutException):
            return "TIMEOUT"
        elif isinstance(error, httpx.ConnectError):
            return "CONNECTION_ERROR"
        elif isinstance(error, httpx.HTTPStatusError):
            if status_code:
                if status_code == 401:
                    return "AUTHENTICATION_ERROR"
                elif status_code == 403:
                    return "AUTHORIZATION_ERROR"
                elif status_code == 429:
                    return "RATE_LIMIT_ERROR"
                elif 500 <= status_code < 600:
                    return "SERVER_ERROR"
                elif 400 <= status_code < 500:
                    return "CLIENT_ERROR"
            return "HTTP_ERROR"
        elif isinstance(error, json.JSONDecodeError):
            return "JSON_PARSE_ERROR"
        elif "network" in str(error).lower():
            return "NETWORK_ERROR"
        else:
            return "UNKNOWN_ERROR"
    
    def _get_recovery_suggestion(self, error_category: str) -> str:
        """Provide recovery suggestions based on error category"""
        suggestions = {
            "TIMEOUT": "Increase timeout value or check network connectivity",
            "CONNECTION_ERROR": "Check internet connection and API endpoint availability",
            "AUTHENTICATION_ERROR": "Verify API key/credentials are valid and not expired",
            "AUTHORIZATION_ERROR": "Check API permissions and subscription status",
            "RATE_LIMIT_ERROR": "Implement exponential backoff or reduce request frequency",
            "SERVER_ERROR": "API provider issue - wait and retry later",
            "CLIENT_ERROR": "Check request format and required parameters",
            "JSON_PARSE_ERROR": "Check API response format and content-type headers",
            "NETWORK_ERROR": "Check internet connectivity and DNS resolution",
            "UNKNOWN_ERROR": "Review error details and contact support if persistent"
        }
        return suggestions.get(error_category, "Review error details and logs")
    
    def _get_performance_category(self, duration_ms: float) -> str:
        """Categorize performance based on duration"""
        if duration_ms < 1000:
            return "EXCELLENT"
        elif duration_ms < 3000:
            return "GOOD"
        elif duration_ms < 10000:
            return "SLOW"
        else:
            return "VERY_SLOW"


# Decorator for automatic API call logging
def track_api_call(api_name: str, endpoint: str = "", method: str = "POST"):
    """Decorator to automatically track API calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            debug_logger = DebugLogger(func.__module__)
            
            # Extract request data from function arguments
            request_data = {}
            if args:
                request_data = {"args": str(args)[:200]}
            if kwargs:
                request_data.update({"kwargs": str(kwargs)[:200]})
            
            call_id = debug_logger.log_api_call_start(
                api_name=api_name,
                endpoint=endpoint or func.__name__,
                method=method,
                request_data=request_data
            )
            
            try:
                result = func(*args, **kwargs)
                debug_logger.log_api_call_success(
                    call_id=call_id,
                    response_data={"result_type": type(result).__name__}
                )
                return result
            except Exception as e:
                debug_logger.log_api_call_failure(call_id=call_id, error=e)
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            debug_logger = DebugLogger(func.__module__)
            
            # Extract request data from function arguments
            request_data = {}
            if args:
                request_data = {"args": str(args)[:200]}
            if kwargs:
                request_data.update({"kwargs": str(kwargs)[:200]})
            
            call_id = debug_logger.log_api_call_start(
                api_name=api_name,
                endpoint=endpoint or func.__name__,
                method=method,
                request_data=request_data
            )
            
            try:
                result = await func(*args, **kwargs)
                debug_logger.log_api_call_success(
                    call_id=call_id,
                    response_data={"result_type": type(result).__name__}
                )
                return result
            except Exception as e:
                debug_logger.log_api_call_failure(call_id=call_id, error=e)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global debug logger instance
debug_logger = DebugLogger("instagram_leadgen")