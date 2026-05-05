"""
Logger Module for HAR MLOps Production Pipeline

Provides centralized logging configuration for the entire pipeline.
Sets up rotating log files with timestamps and clean formatting.

Features:
- Single log file per run (timestamped)
- Rotating log files (5MB max, 3 backups)
- Clean format: [timestamp] logger - level - message
- Automatic log directory creation
- No duplicate handlers

Usage:
    from src.logger import logging
    logging.info("Your message here")
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import PROJECT_ROOT as CONFIG_PROJECT_ROOT
from src.utils.common import get_timestamp

# Constants for log configuration
LOG_DIR = "logs"
LOG_FILE = f"{get_timestamp()}.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Get project root (where run_pipeline.py is)
PROJECT_ROOT = Path(CONFIG_PROJECT_ROOT)
log_dir_path = PROJECT_ROOT / LOG_DIR
log_dir_path.mkdir(parents=True, exist_ok=True)
log_file_path = log_dir_path / LOG_FILE


def get_logger():
    """
    Configure and return the root logger.

    This function sets up a comprehensive logging system that:
    - Logs DEBUG level and above to rotating files
    - Logs INFO level and above to console
    - Automatically rotates log files when they reach 5MB
    - Keeps 3 backup log files
    - Uses timestamped filenames for each run

    Returns:
        logging.Logger: Configured root logger
    """
    logger = logging.getLogger()

    # Only configure if not already configured (prevent duplicate handlers)
    if not logger.handlers:
        # Set root logger to INFO (not DEBUG) to avoid third-party noise
        logger.setLevel(logging.INFO)

        # Define formatter for consistent log message format
        formatter = logging.Formatter(
            "[ %(asctime)s ] %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File handler with rotation - detailed logging
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # File gets DEBUG for our code

        # Console handler - cleaner output
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Silence noisy third-party loggers
        logging.getLogger("git").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("matplotlib").setLevel(logging.WARNING)
        logging.getLogger("h5py").setLevel(logging.WARNING)
        logging.getLogger("tensorflow").setLevel(logging.WARNING)
        logging.getLogger("pydot").setLevel(logging.WARNING)
        logging.getLogger("numexpr").setLevel(logging.WARNING)

    return logger


# Configure logger when module is imported
_logger = get_logger()

# Export the current log file path
CURRENT_LOG_FILE = str(log_file_path)
