"""
AI Exam Manager — Logging Configuration
Structured JSON logging with rotating file handler.
"""
import logging
import json
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for easy parsing and monitoring."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(app):
    """
    Configure structured JSON logging with rotating file handler.
    Only activates when app.debug is False (production/staging).
    In debug mode, Flask's default console logging is used.
    """
    # Always create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # File handler — always active regardless of debug mode
    file_handler = RotatingFileHandler(
        'logs/app.json',
        maxBytes=10 * 1024 * 1024,  # 10MB per file
        backupCount=10               # Keep 10 rotated files
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('AI Exam Manager application started')
