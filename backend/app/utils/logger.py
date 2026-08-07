import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_query(logger: logging.Logger, query: str, response: str, latency_ms: float, sources: int = 0):
    """Log a query operation"""
    logger.info(
        "Query processed",
        extra={
            "extra_data": {
                "query": query[:100],
                "response_length": len(response),
                "latency_ms": latency_ms,
                "sources_found": sources
            }
        }
    )


def log_error(logger: logging.Logger, error: str, error_type: str, context: Dict[str, Any] = None):
    """Log an error with context"""
    log_data = {
        "error_type": error_type,
        "error_message": error
    }
    if context:
        log_data.update(context)

    logger.error(
        f"Error: {error_type}",
        extra={"extra_data": log_data}
    )
