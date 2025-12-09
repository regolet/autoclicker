"""
Centralized logging configuration for the Auto Clicker application.
"""
import logging
import sys
from typing import Optional


def setup_logging(
    log_file: str = "autoclicker_log.txt",
    level: int = logging.INFO,
    console_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Configure and return the application logger.
    
    Args:
        log_file: Path to the log file
        level: Logging level for file handler
        console_level: Logging level for console handler
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("autoclicker")
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # File handler - writes to log file
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}")
    
    # Console handler - writes to stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Module name (will be appended to 'autoclicker.')
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"autoclicker.{name}")
    return logging.getLogger("autoclicker")


# Initialize default logger on import
logger = setup_logging()
