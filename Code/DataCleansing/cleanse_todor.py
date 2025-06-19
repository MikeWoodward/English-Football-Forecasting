#!/usr/bin/env python3
"""
Module for cleansing todor data.

This module provides functions to read, validate, cleanse, and save todor data.
The todor dataset contains historical football match data including scores,
dates, and team names that need to be normalized and validated.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
from utilities import (
    check_clubs_1,  # Validates club names against normalization data
    check_clubs_2,  # Performs additional club name consistency checks
    transform_club_names  # Normalizes club names to standard format
)

import pandas as pd

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_todor(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Read todor data from a file into a pandas DataFrame.

    This function attempts to read a CSV file containing todor match data.
    It includes error handling for common file reading issues and logs
    the process for debugging purposes.

    Args:
        file_path (Path): Path to the todor data file.

    Returns:
        Optional[pd.DataFrame]: DataFrame containing todor data if successful,
            None if there was an error.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    logger.info(f"Reading todor data from {file_path}")
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully read {len(df)} rows from todor data")
        return df
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(
            f"Todor data file not found at {file_path}"
        ) from e
    except pd.errors.EmptyDataError as e:
        logger.error(f"Empty file: {file_path}")
        raise pd.errors.EmptyDataError(
            f"Todor data file is empty: {file_path}"
        ) from e
    except Exception as e:
        logger.error(f"Error reading todor data: {str(e)}")
        raise


def check_todor(df: pd.DataFrame) -> bool:
    """
    Validate the todor DataFrame for correctness.

    This function performs comprehensive validation of the todor dataset,
    including:
    - Checking for required columns
    - Validating data types and formats
    - Checking for null values
    - Verifying club names against normalization data
    - Validating date formats

    Args:
        df (pd.DataFrame): DataFrame to validate.

    Returns:
        bool: True if the DataFrame is valid, False otherwise.

    Raises:
        ValueError: If the DataFrame is empty or has invalid structure.
    """
    logger.info("Checking todor data validity")
    if df.empty:
        raise ValueError("DataFrame is empty")

    # Define required columns for todor dataset
    required_columns = [
        'season', 'league_tier', 'date', 'home_club', 'away_club',
        'home_goals', 'away_goals'
    ]
    
    # Check for missing required columns
    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False

    # Check for null values in required columns and log problematic rows
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        for col, count in null_counts[null_counts > 0].items():
            logger.warning(f"Column '{col}' has {count} null values")
            logger.warning(df[df[col].isnull()])

    # Validate that goals columns contain only numeric values
    for col in ['home_goals', 'away_goals']:
        non_numeric = pd.to_numeric(df[col], errors='coerce').isnull()
        if non_numeric.any():
            invalid_values = df.loc[non_numeric, col].unique()
            logger.warning(
                f"Column '{col}' contains non-numeric values: "
                f"{invalid_values}"
            )

    # Validate date format in the date column
    try:
        pd.to_datetime(df['date'], errors='raise')
    except ValueError as e:
        logger.warning(f"Invalid dates found in 'date' column: {str(e)}")

    # Perform club name validation using utility functions
    # check_clubs_1: Validates against normalization data and stops on error
    # check_clubs_2: Performs additional consistency checks without stopping
    check_clubs_1(matches=df, error_stop=True)
    check_clubs_2(matches=df, error_stop=False)

    logger.info("Todor data validation complete")
    return True


def cleanse_todor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the todor DataFrame.

    This function performs data cleaning operations including:
    - Removing rows with empty dates
    - Adding corrections from todor_corrections file
    - Normalizing club names
    - Removing duplicate entries

    Args:
        df (pd.DataFrame): DataFrame to cleanse.

    Returns:
        pd.DataFrame: Cleaned DataFrame.

    Raises:
        ValueError: If the DataFrame is empty or has invalid structure.
    """
    logger.info("Cleansing todor data")
    if df.empty:
        raise ValueError("DataFrame is empty")

    # Load corrections data for missing or incorrect entries
    todor_corrections = pd.read_csv(
        "../../CleansedData/Corrections and normalization/"
        "todor_corrections.csv"
    )
    
    # Remove rows with empty dates and add corrections
    df = df[df['date'].notna()]
    df = pd.concat([df, todor_corrections])

    # Normalize home and away club names to standard format
    df = transform_club_names(
        df=df,
        source_name="home_club",
        target_name="home_club"
    )
    df = transform_club_names(
        df=df,
        source_name="away_club",
        target_name="away_club"
    )
    # Rename date to match_date
    df = df.rename(columns={'date': 'match_date'})

    # Get the day of week from the match_date column
    df['match_day_of_week'] = (
        pd.to_datetime(df['match_date']).dt.day_name()
    )

    # Remove any duplicate entries that may have been created
    df = df.drop_duplicates()

    return df


def save_todor(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the todor DataFrame to a file.

    This function saves the processed DataFrame to a CSV file,
    creating the output directory if it doesn't exist.

    Args:
        df (pd.DataFrame): DataFrame to save.
        output_path (Path): Path where the DataFrame should be saved.

    Raises:
        IOError: If there is an error writing to the file.
    """
    logger.info(f"Saving todor data to {output_path}")
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info("Successfully saved todor data")
    except IOError as e:
        logger.error(f"Error saving todor data: {str(e)}")
        raise


if __name__ == "__main__":
    # Main execution block for processing todor data
    try:
        # Define input and output file paths
        input_file = Path("../../RawData/Matches/todor/todor.csv")
        output_file = Path("../../CleansedData/Interim/todor.csv")

        # Process the data through the pipeline:
        # 1. Read the data
        # 2. Validate the data structure and content
        # 3. Clean and transform the data
        # 4. Validate the cleaned data
        # 5. Save the processed data
        todor = read_todor(input_file)
        if check_todor(todor):
            todor = cleanse_todor(todor)
            check_todor(todor)
            save_todor(todor, output_file)
        else:
            logger.error("Todor data validation failed")
            sys.exit(1)
    except Exception as e:
        # Log detailed error information including line number
        logger.error(f"Error processing todor data: {str(e)}")
        logger.error(
            f"Error occurred at line "
            f"{traceback.extract_tb(e.__traceback__)[-1].lineno}"
        )
        sys.exit(1) 