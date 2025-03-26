"""Logging functionality for the Meshtastic client."""

import os
import logging
import time
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

# Configure logging
LOG_DIRECTORY = os.path.join(os.path.expanduser("~"), ".meshtastic_client", "logs")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
COMMAND_LOG_FORMAT = "%(asctime)s [COMMAND] %(message)s"

# Ensure log directory exists
os.makedirs(LOG_DIRECTORY, exist_ok=True)

# Store logger instances for reuse
_loggers: Dict[str, logging.Logger] = {}

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: The name of the logger, typically __name__
        
    Returns:
        A configured logger instance
    """
    global _loggers
    
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # Set up file handler
    log_file = os.path.join(LOG_DIRECTORY, f"{name.split('.')[-1]}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024*10, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    _loggers[name] = logger
    return logger


class CommandLogger:
    """Logger specifically for tracking commands."""
    
    def __init__(self):
        """Initialize the command logger."""
        self.logger = logging.getLogger("meshtastic_client.commands")
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Set up file handler
        log_file = os.path.join(LOG_DIRECTORY, "commands.log")
        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024*10, backupCount=5)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(COMMAND_LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Add handler
        self.logger.addHandler(file_handler)
    
    def log_command(self, command: str, channel: int, sender: str, success: bool, response: Optional[str] = None) -> None:
        """Log a command.
        
        Args:
            command: The command that was executed
            channel: The channel the command was executed on
            sender: The sender of the command
            success: Whether the command was successful
            response: The response to the command, if any
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"[{status}] Channel: {channel}, Sender: {sender}, Command: {command}"
        
        if response:
            message += f", Response: {response}"
        
        self.logger.info(message)


# Create a global command logger instance
command_logger = CommandLogger()