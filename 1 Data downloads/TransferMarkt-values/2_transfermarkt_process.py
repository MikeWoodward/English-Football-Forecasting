"""
2_transfermarkt_process.py - TransferMarkt Data Processing Script

This script processes the downloaded TransferMarkt data files and prepares them
for analysis. It performs the following operations:
- Combines all CSV files from different seasons and tiers
- Cleans and standardizes the data
- Converts market values to numeric format
- Handles missing data and outliers
- Creates a consolidated dataset ready for analysis

Data Structure:
- Input: Multiple CSV files in Data-Download/ directory
- Output: Single processed CSV file with cleaned data

Usage:
    python 2_transfermarkt_process.py

Dependencies:
    - pandas: For data manipulation
    - numpy: For numerical operations
    - os: For file operations
    - logging: For logging operations

Author: Mike Woodward
Date: March 2024
Version: 1.0
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path to import cleanup utilities
sys.path.append(
    os.path.join(os.path.dirname(__file__), '..', 'DataSourceCleanUp')
)

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
    # Create Log directory if it doesn't exist
    log_dir = 'Log'
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(
        log_dir,
        f'transfermarkt_process_{timestamp}.log'
    )

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    logging.info(f"Logging initialized. Log file: {log_filename}")


def get_data(
    *,
    data_folder: str = 'Data-Download'
) -> pd.DataFrame:
    """
    Read all CSV files from the specified data folder and merge them into a
    single pandas DataFrame.

    This function searches for all CSV files in the data folder, reads each one,
    and concatenates them into a single DataFrame. It handles potential encoding
    issues and provides detailed logging of the process.

    Args:
        data_folder: Path to the folder containing CSV files.
                    Defaults to 'Data-Download'.

    Returns:
        pd.DataFrame: Combined DataFrame containing all CSV data.

    Raises:
        FileNotFoundError: If the data folder doesn't exist.
        ValueError: If no CSV files are found in the folder.
    """
    # Check if data folder exists
    if not os.path.exists(data_folder):
        raise FileNotFoundError(
            f"Data folder '{data_folder}' not found at line "
            f"{get_data.__code__.co_firstlineno + 15}"
        )

    # Get all CSV files in the folder
    csv_files = [
        f for f in os.listdir(data_folder)
        if f.endswith('.csv') and not f.startswith('.')
    ]

    if not csv_files:
        raise ValueError(
            f"No CSV files found in '{data_folder}' at line "
            f"{get_data.__code__.co_firstlineno + 22}"
        )

    logging.info(f"Found {len(csv_files)} CSV files in {data_folder}")

    # List to store all dataframes
    dataframes = []

    # Read each CSV file
    for csv_file in csv_files:
        try:
            file_path = os.path.join(data_folder, csv_file)
            logging.info(f"Reading file: {csv_file}")

            # Read CSV with error handling for encoding. squad_size,
            # foreigner_count are ints. mean_age is a float so we need to
            # convert it to int. total_market_value is a string for now,
            # so we need to convert it to float.
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                on_bad_lines='warn',
                dtype={
                    'squad_size': int,
                    'foreigner_count': int,
                    'mean_age': float
                },
                na_values=['-', '']
            )

            dataframes.append(df)
            logging.info(
                f"Successfully read {csv_file} with {len(df)} rows"
            )

        except Exception as e:
            logging.error(
                f"Failed to read {csv_file} at line "
                f"{e.__traceback__.tb_lineno}: {e}"
            )
            raise

    # Concatenate all dataframes
    if dataframes:
        combined_df = pd.concat(
            dataframes,
            ignore_index=True,
            sort=False
        )

        # Sort the dataframe by season, league_tier, and club_name
        combined_df = combined_df.sort_values(
            by=['season', 'league_tier', 'club_name'],
            ascending=[True, True, True]
        ).reset_index(drop=True)

        logging.info(
            f"Successfully combined {len(dataframes)} files into "
            f"DataFrame with {len(combined_df)} total rows"
        )
        logging.info(
            "DataFrame sorted by season, league_tier, and club_name"
        )
        return combined_df
    else:
        raise ValueError(
            f"No valid CSV files could be read from '{data_folder}' at line "
            f"{get_data.__code__.co_firstlineno + 85}"
        )




def cleanse_data(*, combined_data: pd.DataFrame) -> pd.DataFrame:
    """
    Cleanse the combined TransferMarkt data.

    This function takes the combined dataframe and performs data cleaning
    operations to prepare it for analysis.

    Args:
        combined_data: The combined dataframe from all CSV files.

    Returns:
        A cleansed dataframe ready for analysis.

    Raises:
        Exception: If any error occurs during data cleansing.
    """
    try:
        # Create a copy of market values to avoid modifying original data
        market_values = combined_data['total_market_value'].copy()

        # Remove currency symbols ($, €) and commas from market value strings
        # This prepares the data for numeric conversion
        market_values = market_values.replace(
            {'\\$': '', '€': '', ',': ''},
            regex=True
        )

        # Convert billions (bn) to actual numeric values
        # Example: "1.5bn" becomes 1500000000
        billions_mask = market_values.str.contains('bn', case=False, na=False)
        market_values[billions_mask] = (
            market_values[billions_mask]
            .str.replace('bn', '', case=False, regex=False)
            .astype(float) * 1_000_000_000
        )

        # Convert millions (m) to actual numeric values
        # Example: "50m" becomes 50000000
        millions_mask = market_values.str.contains('m', case=False, na=False)
        market_values[millions_mask] = (
            market_values[millions_mask]
            .str.replace('m', '', case=False, regex=False)
            .astype(float) * 1_000_000
        )

        # Convert thousands (k) to actual numeric values
        # Example: "500k" becomes 500000
        thousands_mask = market_values.str.contains('k', case=False, na=False)
        market_values[thousands_mask] = (
            market_values[thousands_mask]
            .str.replace('k', '', case=False, regex=False)
            .astype(float) * 1_000
        )

        # Update the dataframe with the converted market values
        combined_data['total_market_value'] = market_values

        # Calculate the fraction of foreign players in each squad
        # This provides a normalized measure of squad internationalization
        combined_data['foreigner_fraction'] = (
            combined_data['foreigner_count'] / combined_data['squad_size']
        )

        # Normalize club names using external utility function
        # This ensures consistent naming across different data sources
        combined_data = transform_club_names(
            df=combined_data,
            source_name='club_name',
            target_name='club_name',
            logger=logging
        )

        return combined_data

    except KeyError as e:
        logging.error(
            f"Missing column error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}. "
            f"Available columns: {list(combined_data.columns)}"
        )
        raise

    except ValueError as e:
        logging.error(
            f"Value conversion error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise

    except TypeError as e:
        logging.error(
            f"Type error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise

    except AttributeError as e:
        logging.error(
            f"Attribute error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise

    except Exception as e:
        logging.error(
            f"Unexpected error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise


if __name__ == "__main__":
    # Set up logging
    setup_logging()

    logging.info("Starting TransferMarkt data processing...")

    try:
        # Load and combine all CSV data
        logging.info("Loading data from CSV files...")
        combined_data = get_data()

        logging.info(f"Data loaded successfully. Shape: {combined_data.shape}")
        logging.info(f"Columns: {list(combined_data.columns)}")
        logging.info(f"Sample data:\n{combined_data.head()}")

        cleansed_data = cleanse_data(combined_data=combined_data)

        # Save the cleansed data to a CSV file
        cleansed_data.to_csv(
            'Data/transfermarkt.csv',
            index=False
        )

        logging.info("TransferMarkt data processing completed successfully")

    except Exception as e:
        logging.error(
            f"Fatal error in main processing at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        exit(1)
