"""
Logging utilities and setup
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set log file path
    if log_file is None:
        log_file = log_dir / "monitor.log"
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


class LogCleaner:
    """Utility class for cleaning old log files"""
    
    def __init__(self, log_dir: str = "data/logs", max_age_days: int = 30):
        self.log_dir = Path(log_dir)
        self.max_age_days = max_age_days
    
    def cleanup_old_logs(self) -> None:
        """Remove log files older than max_age_days"""
        import time
        
        if not self.log_dir.exists():
            return
        
        current_time = time.time()
        max_age_seconds = self.max_age_days * 24 * 3600
        
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.is_file():
                file_age = current_time - log_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        log_file.unlink()
                        logging.info(f"Deleted old log file: {log_file}")
                    except Exception as e:
                        logging.error(f"Failed to delete log file {log_file}: {e}")