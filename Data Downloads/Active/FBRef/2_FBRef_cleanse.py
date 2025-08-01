#!/usr/bin/env python3
"""
Module for cleaning and processing FBRef data.

This module provides functions to read, clean, validate, and save FBRef data.
"""

# Standard library imports
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

# Add parent directory to path to import DataSourceCleanUp
# This allows us to import from the parent directory's modules
sys.path.append(str(Path(__file__).parent.parent))
from DataSourceCleanUp.cleanuputilities import transform_club_names  # noqa: E402

# Configure logging for the module
# Sets up logging format and level for tracking execution progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_fbref() -> pd.DataFrame:
    """
    Read and concatenate all FBRef data from CSV files in the RawData/FBRef
    directory.

    Returns:
        pd.DataFrame: The concatenated FBRef data from all CSV files.

    Raises:
        FileNotFoundError: If the RawData/FBRef directory cannot be found.
        pd.errors.EmptyDataError: If any of the CSV files are empty.
    """
    try:
        # Log the start of the data reading process
        logger.info("Reading FBRef data from CSV files...")
        
        # Define the directory containing the CSV files
        data_dir = Path("Data-league-season")

        # Check if the data directory exists
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_dir}")

        # Initialize list to store individual dataframes
        dfs = []
        
        # Iterate through all CSV files in the directory
        for csv_file in data_dir.glob("*.csv"):
            # Log which file is being processed
            logger.info(f"Reading {csv_file.name}...")
            
            # Read the CSV file into a dataframe
            df = pd.read_csv(csv_file)
            
            # Extract season from filename (characters 3 to 11)
            # Format is typically "1_2023-2024.csv" so we extract "2023-2024"
            season = csv_file.name[2:11]
            df['season'] = season
            
            # Add the dataframe to our list
            dfs.append(df)

        # Check if any CSV files were found
        if not dfs:
            raise FileNotFoundError("No CSV files found in the directory")

        # Concatenate all dataframes into a single dataframe
        # ignore_index=True ensures we get a fresh index
        fbref = pd.concat(dfs, ignore_index=True)
        
        # Log successful completion with row count
        logger.info(f"Successfully read {len(fbref)} rows of FBRef data")
        return fbref

    except FileNotFoundError as e:
        # Handle file/directory not found errors
        logger.error(f"Error accessing files: {str(e)}")
        raise
    except pd.errors.EmptyDataError:
        # Handle empty CSV files
        logger.error("One or more CSV files are empty")
        raise
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error reading FBRef data: {str(e)}")
        raise


def cleanse_fbref(fbref: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process the FBRef dataframe.

    Performs the following operations:
    - Renames columns for consistency
    - Drops unnecessary columns
    - Standardizes match day names

    Args:
        fbref (pd.DataFrame): The raw FBRef dataframe.

    Returns:
        pd.DataFrame: The cleaned FBRef dataframe.
    """
    # Log the start of the cleaning process
    logger.info("Cleaning FBRef data...")

    # Make a copy to avoid modifying the original dataframe
    # This is important for data integrity
    df = fbref.copy()

    # Rename columns to standardize naming conventions
    # Maps original column names to new standardized names
    column_mapping = {
        'away_team': 'away_club',
        'home_team': 'home_club',
        'start_time': 'match_time',
    }
    df = df.rename(columns=column_mapping)

    # Drop unnecessary columns that are not needed for analysis
    # errors='ignore' prevents errors if columns don't exist
    columns_to_drop = ['match_report', 'referee', 'source', 'notes']
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # Standardize match day names from abbreviations to full names
    # This ensures consistency in day-of-week data
    day_mapping = {
        'Sat': 'Saturday',
        'Sun': 'Sunday',
        'Mon': 'Monday',
        'Tue': 'Tuesday',
        'Wed': 'Wednesday',
        'Thu': 'Thursday',
        'Fri': 'Friday'
    }
    df['match_day_of_week'] = df['match_day_of_week'].map(day_mapping)

    # Clean match times by removing timezone information in parentheses
    # Example: "15:00 (GMT)" becomes "15:00"
    df['match_time'] = df['match_time'].str.split("(").str[0]

    # Normalize club names using the external utility function
    # This ensures consistent club naming across the dataset
    df = transform_club_names(
        df=df,
        source_name="home_club",
        target_name="home_club",
        logger=logger
    )
    df = transform_club_names(
        df=df,
        source_name="away_club",
        target_name="away_club",
        logger=logger
    )

    # Set attendance to zero for matches that happened during COVID-19
    covid_mask = (
        (df['match_date'] > '2020-03-01') &
        (df['match_date'] < '2021-05-24') &
        (df['attendance'].isnull())
    )
    df.loc[covid_mask, 'attendance'] = 0

    # Remove any duplicate rows that might exist in the data
    # This ensures data quality and prevents analysis issues
    df = df.drop_duplicates()

    # Convert goal columns to integer type for proper numerical operations
    # This ensures goals are treated as numbers, not strings
    df['home_goals'] = df['home_goals'].astype(int)
    df['away_goals'] = df['away_goals'].astype(int)

    # Reset the index after all cleaning operations
    # This ensures a clean, sequential index
    df = df.reset_index(drop=True)

    # Log completion with final row count
    logger.info(f"Cleaned data now contains {len(df)} rows")
    return df


def check_fbref(fbref: pd.DataFrame) -> None:
    """
    Validate the FBRef dataframe for data quality and completeness.

    Args:
        fbref (pd.DataFrame): The FBRef dataframe to validate.

    Raises:
        ValueError: If the dataframe fails validation checks.
    """
    # Log the start of the validation process
    logger.info("Checking FBRef data...")

    # Check if dataframe is empty - this would indicate a serious problem
    if fbref.empty:
        raise ValueError("Dataframe is empty")

    # Check for null values in required columns
    # These columns are essential for analysis and should not have nulls
    required_columns = [
        'match_date', 'home_goals', 'away_goals',
        'league_tier', 'away_club', 'home_club', 'season'
    ]
    
    # Count null values in each required column
    null_counts = fbref[required_columns].isnull().sum()
    
    # Log warnings for any columns with null values
    for col, count in null_counts.items():
        if count > 0:
            logger.warning(f"Column '{col}' has {count} null values.")

    # Log successful completion of validation
    logger.info("FBRef data validation complete")


def save_fbref(fbref: pd.DataFrame, output_path: Optional[str] = None) -> None:
    """
    Save the FBRef dataframe to disk.

    Args:
        fbref (pd.DataFrame): The FBRef dataframe to save.
        output_path (str, optional): Path to save the file. Defaults to
            '../../CleansedData/Interim/fbref.csv'.

    Raises:
        IOError: If there are issues writing the file.
    """
    # Set default output path if none provided
    if output_path is None:
        output_path = Path("Data/fbref.csv")
    else:
        output_path = Path(output_path)

    try:
        # Create the output directory if it doesn't exist
        # parents=True creates parent directories as needed
        # exist_ok=True prevents errors if directory already exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Log the save operation
        logger.info(f"Saving cleaned FBRef data to {output_path}...")
        
        # Save the dataframe to CSV format
        # index=False prevents saving the dataframe index as a column
        fbref.to_csv(output_path, index=False)
        
        # Log successful completion
        logger.info("Successfully saved cleaned FBRef data")
    except IOError as e:
        # Handle file I/O errors
        logger.error(f"Error saving file: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Main execution block - orchestrates the entire data processing pipeline
        
        # Step 1: Read the raw data from CSV files
        fbref_data = read_fbref()

        # Step 2: Clean and process the data
        cleaned_fbref = cleanse_fbref(fbref_data)

        # Step 3: Reorder the columns for better readability and consistency
        # This ensures columns are in a logical order for analysis
        cleaned_fbref = cleaned_fbref[
            [
                'season', 'league_tier', 'match_date', 'match_day_of_week',
                'attendance', 'venue', 'home_club', 'home_goals', 'away_club',
                'away_goals'
            ]
        ]

        # Step 4: Validate the cleaned data for quality assurance
        check_fbref(cleaned_fbref)

        # Step 5: Save the final cleaned data to disk
        save_fbref(cleaned_fbref)

    except Exception as e:
        # Catch any unexpected errors and log them
        logger.error(f"An error occurred: {str(e)}")
        raise
