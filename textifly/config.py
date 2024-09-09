import os
import json
import logging
from logging.handlers import RotatingFileHandler

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "model_path": "",
    "language": "pt"
}
config ={}

def load_config(config_file=CONFIG_FILE):
    """
    Loads the configuration from a JSON file.

    Args:
        config_file (str, optional): The path to the configuration file.
            Defaults to "config.json".

    Returns:
        dict: The loaded configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If there's an error parsing the JSON data.
    """

    if not os.path.exists(config_file):
        logging.info(f"Configuration file not found: {config_file}")
        create_default_config(config_file)  # Call the function to create the file

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        raise  # Re-raise the exception for clarity
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing configuration file: {e}")
        raise  # Re-raise the exception for handling

    # Validate the loaded configuration (optional)
    # You can add checks here to ensure the data is in the expected format

    return config

def create_default_config(config_file=CONFIG_FILE):
    """
    Creates a default configuration file if it doesn't exist.

    Args:
        config_file (str, optional): The path to the configuration file.
            Defaults to "config.json".
    """

    with open(config_file, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    logging.info(f"Default configuration file created: {config_file}")

def logger_config():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    log_handler = RotatingFileHandler('logs/info.log', maxBytes=5*1024*1024, backupCount=5)
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)