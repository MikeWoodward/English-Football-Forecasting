#!/usr/bin/env python3
"""
Module for cleansing todor data.

This module provides functions to read, validate, cleanse, and save todor data.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_todor(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Read todor data from a file into a pandas DataFrame.

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

    # Check for required columns
    required_columns = [
        'season', 'league_tier', 'date', 'home_club', 'away_club',
        'home_goals', 'away_goals'
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False

    # Check for null values in required columns. Print out row containing null values
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        for col, count in null_counts[null_counts > 0].items():
            logger.warning(f"Column '{col}' has {count} null values")
            logger.warning(df[df[col].isnull()])

    # Check for non-numeric values in goals columns
    for col in ['home_goals', 'away_goals']:
        non_numeric = pd.to_numeric(df[col], errors='coerce').isnull()
        if non_numeric.any():
            invalid_values = df.loc[non_numeric, col].unique()
            logger.warning(
                f"Column '{col}' contains non-numeric values: {invalid_values}"
            )

    # Check for invalid dates
    try:
        pd.to_datetime(df['date'], errors='raise')
    except ValueError as e:
        logger.warning(f"Invalid dates found in 'date' column: {str(e)}")

    # Read in club name normalization file
    club_name_normalization = pd.read_csv(
        "../../CleansedData/Corrections and normalization/club_name_normalization.csv"
    )

    # Report on any clubs (home and away) that are not in the normalization file
    missing_clubs = sorted(set(
        df[~df['home_club'].isin(club_name_normalization['club_name'])]['home_club'].to_list() +
        df[~df['away_club'].isin(club_name_normalization['club_name'])]['away_club'].to_list()
    ))

    if missing_clubs:
        logger.warning(
            f"Clubs not found in club_name_normalization: {missing_clubs}"
        )
        raise ValueError("Clubs not found in club_name_normalization")


    return True


def cleanse_todor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform the todor DataFrame.

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


    # Read in todor corrections file
    todor_corrections = pd.read_csv(
        "../../CleansedData/Corrections and normalization/todor_corrections.csv"
    )
    # Replace df with empty date with todor_corrections
    # First, remove rows where date is empty
    df = df[df['date'].notna()]
    # Then, replace rows where date is empty with todor_corrections
    df = pd.concat([
        df,
        todor_corrections])

    # Read in club name normalization file
    club_name_normalization = pd.read_csv(
        "../../CleansedData/Corrections and normalization/club_name_normalization.csv"
    )

    # Merge club_name_normalization with df on home_club
    df = pd.merge(
        df,
        club_name_normalization,
        left_on='home_club',
        right_on='club_name',
        how='left'
    )
    df = df.drop(columns=['home_club', 'club_name'])
    df = df.rename(columns={'club_name_normalized': 'home_club'})

    # Merge club_name_normalization with df on away_club
    df = pd.merge(
        df,
        club_name_normalization,
        left_on='away_club',
        right_on='club_name',
        how='left'
    )
    df = df.drop(columns=['away_club', 'club_name'])
    df = df.rename(columns={'club_name_normalized': 'away_club'})

    df = df.drop_duplicates()

    return df


def save_todor(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the todor DataFrame to a file.

    Args:
        df (pd.DataFrame): DataFrame to save.
        output_path (Path): Path where the DataFrame should be saved.

    Raises:
        IOError: If there is an error writing to the file.
    """
    logger.info(f"Saving todor data to {output_path}")
    try:
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info("Successfully saved todor data")
    except IOError as e:
        logger.error(f"Error saving todor data: {str(e)}")
        raise


if __name__ == "__main__":
    # Example usage
    try:
        input_file = Path("../../RawData/Matches/todor/todor.csv")
        output_file = Path("../../CleansedData/Interim/todor.csv")

        todor = read_todor(input_file)
        if check_todor(todor):
            todor = cleanse_todor(todor)
            check_todor(todor)
            save_todor(todor, output_file)
        else:
            logger.error("Todor data validation failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing todor data: {str(e)}")
        logger.error(f"Error occurred at line {traceback.extract_tb(e.__traceback__)[-1].lineno}")
        sys.exit(1) 