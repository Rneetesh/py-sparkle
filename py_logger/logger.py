import os
import sys
import datetime
import logging
from rich import print


######################################################## SETUP_LOG_FILE ########################################################
def setuplogfile(logger_name="log", level=logging.INFO):
    """
    Sets up the logger for the particular script.
    Format: Time_stamp-log_level-file_name-line_number-function_name-logger_text

    Args:
        logger_name (str, optional): Name of the logger. Defaults to "log".
        level (str, optional): Log level. Defaults to 'INFO'.

    Returns:
        Logger: The configured logger object.
    """

    # Define the directory for log files
    subdirname = os.path.abspath(os.path.join(os.path.dirname(__file__), "log"))
    dirname = os.path.join(subdirname, logger_name)

    # Create directory if it doesn't exist
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # Create log file name with timestamp
    log_file_timestamp = datetime.datetime.now().strftime("_%Y-%m-%d-%H-%M-%S")
    logfilename = os.path.join(dirname, logger_name + log_file_timestamp + ".log")

    # Create logger object
    log_setup = logging.getLogger(logger_name)

    # Define log message format
    formatter = logging.Formatter(
                                "%(asctime)s-%(levelname)s-%(thread)d-%(module)s-%(lineno)s-%(funcName)s-%(message)s",
                                datefmt="%d/%m/%y_%H:%M:%S"
                            )
    
    # Create file handler for logging to file
    fileHandler = logging.FileHandler(logfilename, mode="w")
    fileHandler.setFormatter(formatter)

    # Create stream handler for logging to console
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(formatter)

    # Set logging level
    log_setup.setLevel(level)

    # Add file handler and stream handler to the logger
    log_setup.addHandler(fileHandler)
    # log_setup.addHandler(streamHandler)
    
    return log_setup


######################################################## read_log_file ########################################################
def read_log_file(logger, severity_level=None):
    """
    Reads and prints the contents of the log file associated with the given logger.

    Args:
        logger (Logger): The logger object whose log file is to be read.
        severity_level (int, optional): Severity level to filter log messages. Defaults to None.
        
    Returns:
        list: List of log lines if severity_level is provided, otherwise None.
    """
    # Get the handlers associated with the logger
    handlers = logger.handlers
    log_lines: list = []

    if severity_level is None:
        # Read and print the entire content of the log file
        for handler in handlers:
            if isinstance(handler, logging.FileHandler):
                log_file_name = handler.baseFilename
                
                try:
                    # Open and read the log file
                    with open(log_file_name, 'r') as file:
                        print(f"Contents of log file '{log_file_name}':")
                        print(file.read())
                
                except FileNotFoundError:
                    print(f"Log file '{log_file_name}' not found.")
    
    else:
        # Read and filter log lines based on severity level
        for handler in handlers:
            if isinstance(handler, logging.FileHandler):
                with open(handler.baseFilename, 'r') as log_file:
                    for line in log_file:
                        parts = line.split('-')
                        log_level = parts[1]

                        if log_level in logging._nameToLevel and logging._nameToLevel[log_level] == severity_level:
                            print(line.strip())
                            log_lines.append(line.strip())

    return log_lines


################################################################################################################
if __name__ == "__main__":
    # Create logger
    logger = setuplogfile("example_log")
    
    # Log messages with different severity levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Read from log file associated with logger and severity levels
    read_log_file(logger)
    read_log_file(logger, logging.INFO)