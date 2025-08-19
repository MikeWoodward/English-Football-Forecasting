"""
4_transfermarkt_process_biweekly_values.py - TransferMarkt Biweekly Values Processing Script

This script processes the downloaded TransferMarkt biweekly values data files and prepares them
for analysis. It performs the following operations:
- Combines all CSV files from different seasons and tiers
- Cleans and standardizes the data
- Converts market values to numeric format
- Handles missing data and outliers
- Creates a consolidated dataset ready for analysis

Data Structure:
- Input: Multiple CSV files in Data-Download-Biweekly-values/ directory
- Output: Single processed CSV file with cleaned data

Usage:
    python 4_transfermarkt_process_biweekly_values.py

Dependencies:
    - pandas: For data manipulation
    - os: For file operations
    - logging: For logging operations

Author: Mike Woodward
Date: March 2024
Version: 1.0
"""

# Standard library imports for data manipulation and file operations
import os
import sys
import logging
from datetime import datetime

# Third-party imports
import pandas as pd

# Add parent directory to path to import cleanup utilities
# This allows access to the cleanuputilities module from a different directory
sys.path.append(
    os.path.join(os.path.dirname(__file__), '..', 'DataSourceCleanUp')
)

# Import the club name transformation utility
from cleanuputilities import transform_club_names


def setup_logging(
    *,
    log_level=logging.INFO
) -> None:
    """
    Set up logging configuration for the data processing application.

    This function configures logging to write to both console and file.
    Logs are saved to a 'Log' folder with timestamped filenames.

    Args:
        log_level: The logging level to use. Defaults to logging.INFO.

    Returns:
        None
    """
    # Create Logs directory if it doesn't exist
    log_dir = 'Logs'
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped log filename to avoid overwriting previous logs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(
        log_dir,
        f'transfermarkt_biweekly_process_{timestamp}.log'
    )

    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),  # Write to file
            logging.StreamHandler()  # Write to console
        ]
    )

    logging.info(f"Logging initialized. Log file: {log_filename}")


def get_data(
    *,
    file_folder: str = 'Data-Download-Biweekly-values'
) -> pd.DataFrame:
    """
    Read all CSV files from the specified data folder and merge them into a
    single pandas DataFrame.

    This function searches for all CSV files in the data folder, reads each one,
    and concatenates them into a single DataFrame. It handles potential encoding
    issues and provides detailed logging of the process.

    Args:
        data_folder: Path to the folder containing CSV files to process.
                    Defaults to 'Data-Download-Biweekly-values'.

    Returns:
        pd.DataFrame: A DataFrame containing all the data from the CSV files.

    Raises:
        FileNotFoundError: If the data folder doesn't exist.
        ValueError: If no CSV files are found in the data folder.
    """

    values = pd.concat([pd.read_csv(os.path.join(file_folder, f)) for f in os.listdir(file_folder) if f.endswith('.csv')])
    return values


def cleanse_data(
    *,
    raw_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean and standardize the raw TransferMarkt biweekly values data.

    This function performs various data cleaning operations including:
    - Removing duplicate records
    - Handling missing values
    - Converting data types
    - Standardizing column names
    - Removing outliers
    - Validating data integrity

    Args:
        raw_data: The raw DataFrame to be cleaned.

    Returns:
        pd.DataFrame: A cleaned and standardized DataFrame ready for analysis.

    Raises:
        ValueError: If the input DataFrame is empty or contains invalid data.
    """

    # Normalize club names
    raw_data = transform_club_names(
        df=raw_data,
        source_name='club_name',
        target_name='club_name',
        logger=logging
    )

    # Fix money data
    market_values = raw_data['transfer_value'].copy()
    market_values = market_values.replace(
        {'€': '', ',': ''},
        regex=True
    )
    # Convert billions (bn) to actual numeric values
    # Example: "1.5bn" becomes 1500000000
    # First, identify rows containing 'bn' in any case
    billions_mask = market_values.str.contains('bn', case=False, na=False)
    # Then convert those values by removing 'bn' and multiplying by 1 billion
    market_values[billions_mask] = (
        market_values[billions_mask]
        .str.replace('bn', '', case=False, regex=False)
        .astype(float) * 1_000_000_000
    )

    # Convert millions (m) to actual numeric values
    # Example: "50m" becomes 50000000
    # First, identify rows containing 'm' in any case
    millions_mask = market_values.str.contains('m', case=False, na=False)
    # Then convert those values by removing 'm' and multiplying by 1 million
    market_values[millions_mask] = (
        market_values[millions_mask]
        .str.replace('m', '', case=False, regex=False)
        .astype(float) * 1_000_000
    )

    # Convert thousands (k) to actual numeric values
    # Example: "500k" becomes 500000
    # First, identify rows containing 'k' in any case
    thousands_mask = market_values.str.contains('k', case=False, na=False)
    # Then convert those values by removing 'k' and multiplying by 1 thousand
    market_values[thousands_mask] = (
        market_values[thousands_mask]
        .str.replace('k', '', case=False, regex=False)
        .astype(float) * 1_000
    )

    # Update the dataframe with the converted market values
    # This replaces the original string values with numeric equivalents
    raw_data['transfer_value'] = market_values

    raw_data = raw_data.sort_values(by=['club_name', 'value_date'])

    return raw_data



if __name__ == "__main__":
    # Set up logging
    setup_logging()
    
    file_folder = 'Data-Download-Biweekly-values'
    # if the folder doesn't exist, flag an error and stop
    if not os.path.exists(file_folder):
        logging.error(f"Data folder {file_folder} does not exist")
        sys.exit(1)
    
    try:
        logging.info("Starting TransferMarkt biweekly values data processing")
        
        # Get the raw data
        logging.info("Loading raw data...")
        raw_data = get_data(file_folder=file_folder)
        
        # Clean the data
        logging.info("Cleaning data...")
        cleaned_data = cleanse_data(raw_data=raw_data)

        # Save the cleaned data to a file
        cleaned_data.to_csv(
            'Data/transfermarkt_biweekly_values.csv',
            index=False
        )
        
        logging.info("Data processing completed successfully")
        
    except Exception as e:
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}: {e}")
        sys.exit(1)
