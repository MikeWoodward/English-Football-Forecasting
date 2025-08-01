import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging() -> logging.Logger:
    """
    Sets up logging configuration and creates Logs directory.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create Logs directory if it doesn't exist
    logs_dir = Path("Logs")
    logs_dir.mkdir(exist_ok=True)

    # Create a unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"attendance_violins_{timestamp}.log"

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    return logger


# Initialize logger
logger = setup_logging()


def read_data(file_name: str) -> Optional[pd.DataFrame]:
    """
    Reads in attendance data from a file and returns a Pandas dataframe.

    Args:
        file_name (str): Path to the attendance data file

    Returns:
        Optional[pd.DataFrame]: Raw attendance data or None if error occurs
    """
    logger.info(f"Starting to read data from file: {file_name}")

    try:
        # Try to read the file with pandas
        # This will automatically detect common formats like CSV, Excel, etc.
        data = pd.read_csv(file_name, low_memory=False)
        data['attendance'] = data['attendance'].astype(int)

        logger.info(f"Successfully loaded data from {file_name}")
        logger.info(f"Data shape: {data.shape}")
        logger.info(f"Columns: {list(data.columns)}")

        # Log data summary
        logger.info(f"Data types: {dict(data.dtypes)}")
        logger.info(f"Missing values: {data.isnull().sum().to_dict()}")

        return data

    except FileNotFoundError:
        error_msg = f"File '{file_name}' not found."
        logger.error(error_msg)
        print(error_msg)
        return None
    except Exception as e:
        error_msg = f"Error reading file '{file_name}': {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return None


def process_data(raw_data: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Processes the data so it's in a format suitable for plotting.

    Args:
        raw_data (pd.DataFrame): Raw attendance data

    Returns:
        Optional[pd.DataFrame]: Processed attendance data or None if error
        occurs
    """
    # TODO: Implement data processing for violin plots
    logger.info("Starting data processing for violin plots")

    # Stub implementation - to be completed
    return raw_data


def plot_save_data(processed_data: pd.DataFrame) -> None:
    """
    Plots the data and saves charts to the Plots folder.

    Args:
        processed_data (pd.DataFrame): Processed attendance data
    """
    # TODO: Implement violin plot creation and saving
    logger.info("Starting violin plot creation and saving")

    # Stub implementation - to be completed
    pass


# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the functions
    logger.info("Starting attendance violins script")

    raw_data_file: str = os.path.join(
        "..", "Data Preparation", 'Data', 'match_attendance.csv'
    )
    raw_data: Optional[pd.DataFrame] = read_data(raw_data_file)
    processed_data: Optional[pd.DataFrame] = (
        process_data(raw_data) if raw_data is not None else None
    )
    if processed_data is not None:
        plot_save_data(processed_data)

    logger.info("Script completed")
