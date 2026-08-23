import logging
import os
from datetime import datetime

# Define custom SUCCESS level
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kws)

logging.Logger.success = success

class ActionLogger:
    _initialized = False
    _logger = None

    @classmethod
    def setup_logger(cls, log_file: str = None) -> logging.Logger:
        """Sets up the custom application logger.
        
        Args:
            log_file (str): Absolute or relative path to the log file.
            
        Returns:
            logging.Logger: The configured Logger instance.
        """
        if cls._initialized and cls._logger:
            return cls._logger

        if log_file is None:
            # Default to logs/esim_manager.log in the project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_dir = os.path.join(base_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "esim_manager.log")
        else:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

        logger = logging.getLogger("esim_manager")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # Clear any existing handlers to prevent duplicate logging
        if logger.handlers:
            logger.handlers.clear()

        # Custom Formatter: 2026-08-23 17:45:12 | INFO | Environment scan started
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to initialize file logger: {e}")

        # Stream/Console Handler for debugging/CLI output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        cls._logger = logger
        cls._initialized = True
        return logger

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """Returns the configured logger instance. If not initialized, configures it with defaults."""
        if not cls._initialized:
            return cls.setup_logger()
        return cls._logger

