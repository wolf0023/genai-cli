import logging
import os
from datetime import datetime

from const import LOG_FORMAT, LOG_DIR, LOG_TIME_FORMAT

class Logger:
    """ Logger class for genai-cli.
    Attributes:
        log_dir (str): Directory for storing log files.
        init_time (str): Initialization time for log file naming.
        log_file (str): Path to the log file.
        logger (logging.Logger): Configured logger instance.
    """
    def __init__(self, logging_level: int = logging.INFO):
        self.log_dir: str = os.path.expanduser(LOG_DIR)
        self.init_time: str = datetime.now().strftime(LOG_TIME_FORMAT)

        # Create log directory if it doesn't exist
        self.log_file: str = os.path.join(self.log_dir, f"genai-cli_{self.init_time}.log")
        os.makedirs(self.log_dir, exist_ok=True)

        self.logger = logging.getLogger("genai-cli")
        self.logger.setLevel(logging_level)

        # Set up file handler for logging
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.logger.addHandler(file_handler)
