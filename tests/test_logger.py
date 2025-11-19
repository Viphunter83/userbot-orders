"""Tests for logger module."""

import pytest
from pathlib import Path
from src.utils.logger import setup_logger, get_logger


def test_logger_setup():
    """Test logger setup."""
    setup_logger(log_level="INFO")
    logger = get_logger()
    assert logger is not None
    
    # Test logging
    logger.info("Test log message")


def test_logger_file_output(tmp_path):
    """Test logger file output."""
    log_file = tmp_path / "test.log"
    setup_logger(log_level="DEBUG", log_file=log_file)
    logger = get_logger()
    
    logger.info("Test message to file")
    
    # Check if file was created
    assert log_file.exists()

