"""
Exception Module for HAR MLOps Production Pipeline

Custom exception handling with detailed error tracking.
"""

import logging
import sys


def error_message_detail(error: Exception, error_detail: sys) -> str:
    """
    Extracts detailed error information including file name, line number, and error message.

    Args:
        error: The exception that occurred
        error_detail: The sys module to access traceback details

    Returns:
        Formatted error message string
    """
    _, _, exc_tb = error_detail.exc_info()

    if exc_tb is not None:
        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
        error_message = (
            f"Error occurred in python script: [{file_name}] "
            f"at line number [{line_number}]: {str(error)}"
        )
    else:
        error_message = f"Error: {str(error)}"

    logging.error(error_message)
    return error_message


class MLOpsException(Exception):
    """
    Custom exception class for HAR MLOps pipeline errors.
    """

    def __init__(self, error_message: str, error_detail: sys):
        """
        Initialize MLOpsException with detailed error message.

        Args:
            error_message: String describing the error
            error_detail: The sys module to access traceback details
        """
        super().__init__(error_message)
        self.error_message = error_message_detail(error_message, error_detail)

    def __str__(self) -> str:
        """Returns the string representation of the error message."""
        return self.error_message
