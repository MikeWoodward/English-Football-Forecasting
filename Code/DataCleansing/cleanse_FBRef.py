#!/usr/bin/env python3
"""
Module for cleaning and processing FBRef data.

This module provides functions to read, clean, validate, and save FBRef data.
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


def read_fbref() -> pd.DataFrame:
    """
    Read and concatenate all FBRef data from CSV files in the RawData/FBRef directory.

    Returns:
        pd.DataFrame: The concatenated FBRef data from all CSV files.

    Raises:
        FileNotFoundError: If the RawData/FBRef directory cannot be found.
        pd.errors.EmptyDataError: If any of the CSV files are empty.
    """
    try:
        logger.info("Reading FBRef data from CSV files...")
        data_dir = Path("../../RawData/Matches/FBRef")
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_dir}")
            
        # Read all CSV files in the directory
        dfs = []
        for csv_file in data_dir.glob("*.csv"):
            logger.info(f"Reading {csv_file.name}...")
            df = pd.read_csv(csv_file)
            # Extract season from filename (characters 3 to 11)
            season = csv_file.name[2:11]
            df['season'] = season
            dfs.append(df)
            
        if not dfs:
            raise FileNotFoundError("No CSV files found in the directory")
            
        # Concatenate all dataframes
        fbref = pd.concat(dfs, ignore_index=True)
        logger.info(f"Successfully read {len(fbref)} rows of FBRef data")
        return fbref
        
    except FileNotFoundError as e:
        logger.error(f"Error accessing files: {str(e)}")
        raise
    except pd.errors.EmptyDataError:
        logger.error("One or more CSV files are empty")
        raise
    except Exception as e:
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
    logger.info("Cleaning FBRef data...")
    
    # Make a copy to avoid modifying the original
    df = fbref.copy()
    
    # Rename columns
    column_mapping = {
        'date': 'match_date',
        'away_team': 'away_club',
        'home_team': 'home_club',
        'start_time': 'match_time',
        'dayofweek': 'match_day'
    }
    df = df.rename(columns=column_mapping)
    
    # Drop unnecessary columns
    columns_to_drop = ['match_report', 'referee', 'source', 'notes']
    df = df.drop(columns=columns_to_drop, errors='ignore')
    
    # Standardize match day names
    day_mapping = {
        'Sat': 'Saturday',
        'Sun': 'Sunday',
        'Mon': 'Monday',
        'Tue': 'Tuesday',
        'Wed': 'Wednesday',
        'Thu': 'Thursday',
        'Fri': 'Friday'
    }
    df['match_day'] = df['match_day'].map(day_mapping)
    
    # Normalize club names
    try:
        normalization_path = Path(
            "../../CleansedData/Corrections and normalization/club_name_normalization.csv"
        )
        logger.info(f"Reading club name normalization file from {normalization_path}...")
        club_name_normalization = pd.read_csv(normalization_path)
    except Exception as e:
        logger.error(f"Error reading club name normalization file: {str(e)}")
        raise

    # Normalize away_club
    df = df.merge(
        club_name_normalization,
        left_on="away_club",
        right_on="club_name",
        how="left"
    )
    df = df.drop(columns=["away_club", "club_name"], errors="ignore")
    df = df.rename(columns={"club_name_normalized": "away_club"})

    # Normalize home_club
    df = df.merge(
        club_name_normalization,
        left_on="home_club",
        right_on="club_name",
        how="left"
    )
    df = df.drop(columns=["home_club", "club_name"], errors="ignore")
    df = df.rename(columns={"club_name_normalized": "home_club"})

    # Remove any duplicate rows
    df = df.drop_duplicates()
    
    # Reset the index after cleaning
    df = df.reset_index(drop=True)
    
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
    logger.info("Checking FBRef data...")
    
    # Check if dataframe is empty
    if fbref.empty:
        raise ValueError("Dataframe is empty")
    
    # Check for null values in required columns
    required_columns = [
        'match_date', 'home_goals', 'away_goals',
        'league_tier', 'away_club', 'home_club', 'season'
    ]
    null_counts = fbref[required_columns].isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            logger.warning(f"Column '{col}' has {count} null values.")
    
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
    if output_path is None:
        output_path = Path("../../CleansedData/Interim/fbref.csv")
    else:
        output_path = Path(output_path)
    
    try:
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving cleaned FBRef data to {output_path}...")
        fbref.to_csv(output_path, index=False)
        logger.info("Successfully saved cleaned FBRef data")
    except IOError as e:
        logger.error(f"Error saving file: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Read the data
        fbref_data = read_fbref()
        
        # Clean the data
        cleaned_fbref = cleanse_fbref(fbref_data)
        
        # Reorder the columns
        cleaned_fbref = cleaned_fbref[
            [
                'season', 'league_tier', 'match_date', 'match_day', 'attendance',
                'venue', 'home_club', 'home_goals', 'away_club', 'away_goals'
            ]
        ]

        # Check the data
        check_fbref(cleaned_fbref)
        
        # Save the data
        save_fbref(cleaned_fbref)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise 