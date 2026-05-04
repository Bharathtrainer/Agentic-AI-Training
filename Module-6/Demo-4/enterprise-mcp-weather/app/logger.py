import logging
import sys

def setup_logger(name: str) -> logging.Logger:
    """Configures and returns an enterprise-grade logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create a console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    # Define the enterprise log format: [Timestamp] - [Module] - [Level] - Message
    formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Prevent duplicate logs if initialized multiple times
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger