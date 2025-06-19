#!/usr/bin/env python3
"""
Module for cleansing transfer value data from multiple sources.

This module provides functions to read, cleanse, validate, and save transfer
value data from various sources into a standardized format. The data includes
squad information such as size, age, foreign player count, and market values
across different seasons and league tiers.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional
from utilities import check_clubs_1, check_clubs_2, transform_club_names

# Configure logging with timestamp, module name, and log level for better
# debugging and traceability
logging.basicConfig(
    level=logging.INFO,
    format=(
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(message)s'
    )
)
logger = logging.getLogger(__name__)


def read_transfer_values() -> pd.DataFrame:
    """
    Read transfer value data from multiple sources and combine into a single
    DataFrame.

    This function reads all CSV files from the transfer values directory and
    combines them into a single DataFrame. It ensures all required files exist
    and handles potential file reading errors.

    Returns:
        pd.DataFrame: Combined transfer values data from all sources.

    Raises:
        FileNotFoundError: If required input files are not found.
        pd.errors.EmptyDataError: If input files are empty.
    """
    logger.info("Reading transfer values from source files")
    
    # Define the path to the transfer values directory relative to the script
    # location for better portability
    transfer_values_dir = Path("../../RawData/Matches/TransferValues")
    
    if not transfer_values_dir.exists():
        msg = f"Transfer values directory not found: {transfer_values_dir}"
        raise FileNotFoundError(msg)
    
    # Get all CSV files in the directory to process multiple data sources
    csv_files = list(transfer_values_dir.glob("*.csv"))
    
    if not csv_files:
        msg = f"No CSV files found in {transfer_values_dir}"
        raise FileNotFoundError(msg)
    
    # Read and concatenate all CSV files into a single DataFrame
    # ignore_index=True ensures proper row indexing after concatenation
    transfer_values = pd.concat(
        [pd.read_csv(file) for file in csv_files],
        ignore_index=True
    )
    
    logger.info(f"Successfully read {len(csv_files)} files")
    logger.info(f"Combined DataFrame shape: {transfer_values.shape}")
    
    return transfer_values


def cleanse_transfer_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the transfer values DataFrame.

    This function performs the following operations:
    1. Normalizes club names using a reference mapping to ensure consistency
    2. Standardizes column names for better data organization
    3. Removes unnecessary columns to reduce data complexity
    4. Removes duplicate entries to ensure data integrity

    Args:
        df (pd.DataFrame): Raw transfer values DataFrame to be cleansed.

    Returns:
        pd.DataFrame: Cleaned and standardized transfer values DataFrame.

    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    logger.info("Cleansing transfer values data")
    
    # Transform club names to ensure consistent naming across all data sources
    # This helps in joining with other datasets later
    df = transform_club_names(
        df=df,
        source_name="club_name",
        target_name="club_name"
    )

    # Standardize column name for league tier to match naming conventions
    # in other datasets
    df = df.rename(columns={"tier": "league_tier"})

    # Remove redundant league column as tier information is sufficient
    # and more standardized across different data sources
    df = df.drop(columns=["league"], errors="ignore")

    # Remove any duplicate entries to ensure data integrity and prevent
    # double-counting in subsequent analyses
    df = df.drop_duplicates()

    return df


def check_transfer_values(df: pd.DataFrame) -> bool:
    """
    Validate the contents of the transfer values DataFrame.

    This function performs the following validations:
    1. Checks for null values in required columns to ensure data completeness
    2. Ensures all critical data fields are present for analysis

    Args:
        df (pd.DataFrame): DataFrame to be validated.

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        ValueError: If validation checks fail.
    """
    logger.info("Checking transfer values data")

    # Define required columns that must not contain null values
    # These columns are essential for subsequent analysis
    required_columns = [
        'squad_size',      # Number of players in squad
        'mean_age',        # Average age of squad
        'foreigner_count', # Number of foreign players
        'total_market_value', # Total squad market value
        'season',          # Season identifier
        'league_tier',     # League division level
        'club_name'        # Standardized club name
    ]
    
    # Check each required column for null values to ensure data quality
    # and prevent issues in downstream analysis
    for col in required_columns:
        if df[col].isnull().any():
            msg = f"Column {col} contains null values"
            raise ValueError(msg)

    return True


def save_transfer_values(
    df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """
    Save the transfer values DataFrame to a CSV file.

    This function handles the saving of processed data to a CSV file,
    creating necessary directories if they don't exist and handling
    potential file system errors.

    Args:
        df (pd.DataFrame): DataFrame to be saved.
        output_path (Optional[Path]): Path to save the CSV file. If None,
            uses default path.

    Raises:
        IOError: If file cannot be written.
        PermissionError: If no permission to write to specified location.
    """
    # Use default path if none provided, ensuring consistent output location
    if output_path is None:
        output_path = Path("../../CleansedData/Interim/transfer-values.csv")
    
    # Create the output directory if it doesn't exist to prevent write errors
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved transfer values to {output_path}")
    except (IOError, PermissionError) as e:
        logger.error(f"Failed to save transfer values: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Read the data from multiple source files
        transfer_values = read_transfer_values()
        
        # Cleanse and standardize the data
        transfer_values = cleanse_transfer_values(transfer_values)
        
        # Validate the processed data
        if not check_transfer_values(transfer_values):
            logger.error("Transfer values validation failed")
            exit(1)
        
        # Save the processed data to the output location
        save_transfer_values(transfer_values)
        logger.info("Transfer values processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing transfer values: {str(e)}")
        raise 