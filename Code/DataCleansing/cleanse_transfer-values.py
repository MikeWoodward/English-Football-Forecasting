#!/usr/bin/env python3
"""
Module for cleansing transfer value data from multiple sources.

This module provides functions to read, cleanse, validate, and save transfer
value data from various sources into a standardized format.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_transfer_values() -> pd.DataFrame:
    """
    Read transfer value data from multiple sources and combine into a single
    DataFrame.

    Returns:
        pd.DataFrame: Combined transfer values data from all sources.

    Raises:
        FileNotFoundError: If required input files are not found.
        pd.errors.EmptyDataError: If input files are empty.
    """
    logger.info("Reading transfer values from source files")
    
    # Define the path to the transfer values directory
    transfer_values_dir = Path("../../RawData/Matches/TransferValues")
    
    if not transfer_values_dir.exists():
        raise FileNotFoundError(
            f"Transfer values directory not found: {transfer_values_dir}"
        )
    
    # Get all CSV files in the directory
    csv_files = list(transfer_values_dir.glob("*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {transfer_values_dir}"
        )
    
    # Read and concatenate all CSV files
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
    1. Normalizes club names using a reference mapping
    2. Standardizes column names
    3. Removes unnecessary columns
    4. Removes duplicate entries

    Args:
        df (pd.DataFrame): Raw transfer values DataFrame to be cleansed.

    Returns:
        pd.DataFrame: Cleaned and standardized transfer values DataFrame.

    Raises:
        ValueError: If required columns are missing or data is invalid.
    """
    logger.info("Cleansing transfer values data")
    
    # Load club name normalization mapping from reference file
    club_name_normalization = pd.read_csv(
        "../../CleansedData/Corrections and normalization/"
        "club_name_normalization.csv"
    )

    # Merge with normalization mapping to standardize club names
    df = df.merge(
        club_name_normalization,
        left_on="club_name",
        right_on="club_name",
        how="left"
    )
    # Replace original club names with normalized versions
    df = df.drop(columns=["club_name"], errors="ignore")
    df = df.rename(columns={"club_name_normalized": "club_name"})    

    # Standardize column name for league tier
    df = df.rename(columns={"tier": "league_tier"})

    # Remove redundant league column as tier information is sufficient
    df = df.drop(columns=["league"], errors="ignore")

    # Remove any duplicate entries to ensure data integrity
    df = df.drop_duplicates()

    return df


def check_transfer_values(df: pd.DataFrame) -> bool:
    """
    Validate the contents of the transfer values DataFrame.

    This function performs the following validations:
    1. Checks for null values in required columns
    2. Ensures all critical data fields are present

    Args:
        df (pd.DataFrame): DataFrame to be validated.

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        ValueError: If validation checks fail.
    """
    logger.info("Checking transfer values data")

    # Define required columns that must not contain null values
    required_columns = [
        'squad_size',      # Number of players in squad
        'mean_age',        # Average age of squad
        'foreigner_count', # Number of foreign players
        'total_market_value', # Total squad market value
        'season',          # Season identifier
        'league_tier',     # League division level
        'club_name'        # Standardized club name
    ]
    
    # Check each required column for null values
    for col in required_columns:
        if df[col].isnull().any():
            raise ValueError(f"Column {col} contains null values")

    return True


def save_transfer_values(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Save the transfer values DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): DataFrame to be saved.
        output_path (Optional[Path]): Path to save the CSV file. If None,
            uses default path.

    Raises:
        IOError: If file cannot be written.
        PermissionError: If no permission to write to specified location.
    """
    if output_path is None:
        output_path = Path("../../CleansedData/Interim/transfer-values.csv")
    
    # Create the output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved transfer values to {output_path}")
    except (IOError, PermissionError) as e:
        logger.error(f"Failed to save transfer values: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Read the data
        transfer_values = read_transfer_values()
        
        # Cleanse the data
        transfer_values = cleanse_transfer_values(transfer_values)
        
        # Check the data
        if not check_transfer_values(transfer_values):
            logger.error("Transfer values validation failed")
            exit(1)
        
        # Save the data
        save_transfer_values(transfer_values)
        logger.info("Transfer values processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing transfer values: {str(e)}")
        raise 