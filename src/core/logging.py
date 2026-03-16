"""
Centralized logging configuration for the Frontier backend.

Provides setup_logging() to initialize the logging system and get_logger()
for consistent logger creation across modules.
"""

import logging
import sys
from typing import Optional

_logging_initialized = False


def setup_logging(level: Optional[str] = None, format_str: Optional[str] = None) -> None:
    """
    Initialize the logging system with the specified configuration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               Defaults to config value or INFO.
        format_str: Log format string. Defaults to config value or standard format.
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    from core.config import get_config
    config = get_config()
    
    log_level = level or config.log_level
    log_format = format_str or config.log_format
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S"))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(handler)
    
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("uvicorn.access").setLevel(numeric_level)
    
    _logging_initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name, typically __name__ of the calling module.
        
    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
