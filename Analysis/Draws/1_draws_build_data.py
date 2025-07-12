"""
Data building module for draws analysis.

This module provides functions to read, validate, and save match data from
multiple sources for draws analysis.
"""

import logging
import os
import sys
import pandas as pd
from typing import Optional

# Import analysis utilities for data validation
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Utilities'))
from analysisutilities import (
    SeasonData,
    check_clubs_1,
    check_clubs_2
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_data(*, todor_path: str, enfa_path: Optional[str] = None) -> pd.DataFrame:
    """
    Read data from todor and optionally enfa CSV files,
    merge them, and remove duplicates.

    Args:
        todor_path: Path to the todor CSV file.
        enfa_path: Path to the enfa CSV file. If None, only todor data is used.

    Returns:
        pd.DataFrame: Merged and deduplicated match data.

    Raises:
        FileNotFoundError: If either CSV file does not exist.
        pd.errors.EmptyDataError: If either CSV file is empty.
        pd.errors.ParserError: If either CSV file cannot be parsed.
        ValueError: If data cannot be merged or processed.
    """
    try:
        logger.info("Starting data retrieval and merging process")

        # Read todor data
        logger.info(f"Reading todor data from {todor_path}")
        if not os.path.exists(todor_path):
            error_msg = f"Todor file not found: {todor_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        todor_data = pd.read_csv(todor_path)
        logger.info(f"Loaded {len(todor_data)} rows from todor data")

        # Read enfa data if provided
        if enfa_path:
            logger.info(f"Reading enfa data from {enfa_path}")
            if not os.path.exists(enfa_path):
                error_msg = f"ENFA file not found: {enfa_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            efl_data = pd.read_csv(enfa_path)
            logger.info(
                f"Loaded {len(efl_data)} rows from EFL data"
            )
        else:
            efl_data = pd.DataFrame()

        # Merge the datasets
        logger.info("Merging datasets")
        merged_data = pd.concat([todor_data, efl_data], ignore_index=True)
        logger.info(
            f"Merged data contains {len(merged_data)} rows"
        )

        # Remove duplicates
        logger.info("Removing duplicate records")
        initial_count = len(merged_data)
        merged_data = merged_data.drop_duplicates()
        final_count = len(merged_data)
        duplicates_removed = initial_count - final_count

        # Ensure league_tier is integer
        merged_data['league_tier'] = merged_data['league_tier'].astype(int)

        logger.info(
            f"Removed {duplicates_removed} duplicate records. "
            f"Final dataset contains {final_count} rows"
        )

        if merged_data.empty:
            error_msg = "Merged dataset is empty after deduplication"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Data retrieval and merging completed successfully")
        return merged_data

    except pd.errors.EmptyDataError as e:
        error_msg = f"CSV file is empty: {str(e)}"
        logger.error(error_msg)
        raise
    except pd.errors.ParserError as e:
        error_msg = f"Error parsing CSV file: {str(e)}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Unexpected error in get_data: {str(e)}"
        logger.error(error_msg)
        raise


def check_data(*, data: pd.DataFrame) -> bool:
    """
    Perform comprehensive data validation checks on the merged dataset.

    This function validates:
    1. Seasons present and consistent
    2. Leagues present and consistent
    3. Teams per season match expected counts
    4. Games per season match expected counts

    Args:
        data: DataFrame containing the merged match data.

    Returns:
        bool: True if all checks pass, False otherwise.

    Raises:
        ValueError: If any validation check fails (stops processing).
    """
    try:
        logger.info("Starting comprehensive data validation")

        # Check the clubs are consistent
        # Check 1: check_clubs_1
        if not check_clubs_1(matches=data, error_stop=True, logger=logger):
            error_msg = "Club count validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)
        # Check 2: check_clubs_2
        if not check_clubs_2(matches=data, error_stop=True, logger=logger):
            error_msg = "Club count validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Initialize SeasonData for reference validation
        season_data = SeasonData(logger=logger)

        # Check each season has the correct leagues
        if not season_data.check_leagues_seasons(matches=data):
            error_msg = "League seasons validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check each season has the correct number of clubs
        if not season_data.check_leagues_seasons_clubs(matches=data):
            error_msg = "League seasons clubs validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check each season has the correct number of matches
        if not season_data.check_leagues_seasons_matches(matches=data):
            error_msg = "League seasons matches validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("All data validation checks passed successfully")
        return True

    except Exception as e:
        error_msg = f"Data validation failed: {str(e)}"
        logger.error(error_msg)
        raise


def save_data(*, data: pd.DataFrame, output_path: str) -> None:
    """
    Save the validated data to the specified output path.

    Args:
        data: DataFrame containing the validated match data.
        output_path: Path where the data should be saved.

    Raises:
        ValueError: If data is empty or invalid.
        OSError: If the file cannot be written.
    """
    try:
        logger.info(f"Saving validated data to {output_path}")

        # Ensure the output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")

        # Validate data before saving
        if data.empty:
            error_msg = "Cannot save empty dataset"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Save the data to CSV
        data.to_csv(output_path, index=False)
        logger.info(
            f"Successfully saved {len(data)} rows to {output_path}"
        )

    except OSError as e:
        error_msg = f"Error writing file {output_path}: {str(e)}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Unexpected error saving data: {str(e)}"
        logger.error(error_msg)
        raise


if __name__ == "__main__":
    # Example usage of the data building functions
    try:
        # Define file paths
        todor_file = (
            "../../Data downloads/Active/Todor/Data/todor_cleansed.csv"
        )
        enfa_file = (
            "../../Data downloads/Active/ENFA/Data/enfa_cleansed.csv"
        )
        output_file = "data/merged_match_data.csv"

        # Get and merge data
        logger.info("Starting data building process")
        merged_data = get_data(
            todor_path=todor_file,
            enfa_path=enfa_file
        )

        # Validate data
        if check_data(data=merged_data):
            # Save validated data
            save_data(data=merged_data, output_path=output_file)
            logger.info("Data building process completed successfully")
        else:
            logger.error("Data validation failed - process stopped")

    except Exception as e:
        logger.error(f"Data building process failed: {str(e)}")
        raise 