#!/usr/bin/env python3
"""
Module for cleaning and processing Football-data data.

This module provides functions to read, clean, validate, and save Football-data.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional
from utilities import check_clubs_1, check_clubs_2, transform_club_names

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_football_data() -> pd.DataFrame:
    """
    Read and concatenate all Football-data from CSV files in the RawData directory.

    Returns:
        pd.DataFrame: The concatenated Football-data from all CSV files.

    Raises:
        FileNotFoundError: If the RawData directory cannot be found.
        pd.errors.EmptyDataError: If any of the CSV files are empty.
    """
    try:
        logger.info("Reading Football-data from CSV files...")
        data_dir = Path("../../RawData/Matches/Football-data")
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_dir}")
            
        # Read all CSV files in the directory
        dfs = []
        for csv_file in data_dir.glob("*.csv"):
            logger.info(f"Reading {csv_file.name}...")
            df = pd.read_csv(csv_file)
            
            # Extract league_tier from first character of filename
            league_tier = csv_file.stem[0]
            df['league_tier'] = league_tier
            
            # Extract season from characters 3 to 11 of filename
            season = csv_file.stem[2:11]
            df['season'] = season
            
            dfs.append(df)
            
        if not dfs:
            raise FileNotFoundError("No CSV files found in the directory")
            
        # Concatenate all dataframes
        football_data = pd.concat(dfs, ignore_index=True)
        logger.info(f"Successfully read {len(football_data)} rows of Football-data")
        return football_data
        
    except FileNotFoundError as e:
        logger.error(f"Error accessing files: {str(e)}")
        raise
    except pd.errors.EmptyDataError:
        logger.error("One or more CSV files are empty")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading Football-data: {str(e)}")
        raise


def cleanse_football_data(football_data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process the Football-data dataframe.

    Args:
        football_data (pd.DataFrame): The raw Football-data dataframe.

    Returns:
        pd.DataFrame: The cleaned Football-data dataframe with only the specified
            columns: Date, HomeTeam, AwayTeam, match_date, match_time, season,
            league_tier.

    Raises:
        KeyError: If any of the required columns are not present in the dataframe.
    """
    try:
        logger.info("Cleaning Football-data...")
        
        # Make a copy to avoid modifying the original
        df = football_data.copy()
        
        # Define columns to keep
        columns_to_keep = [
            'HomeTeam', 'AwayTeam', 'match_date', 'match_time',
            'season', 'league_tier', 'FTHG', 'FTAG'
        ]
        
        # Check if all required columns exist
        missing_columns = [col for col in columns_to_keep if col not in df.columns]
        if missing_columns:
            raise KeyError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Keep only the specified columns
        df = df[columns_to_keep]
        
        # Normalize club names
        df = transform_club_names(
            df=df,
            source_name="HomeTeam",
            target_name="home_club"
        )
        df = transform_club_names(
            df=df,  
            source_name="AwayTeam",
            target_name="away_club"
        )

        # Rename columns - FTHG to home_goals, FTAG to away_goals
        df = df.rename(columns={"FTHG": "home_goals", "FTAG": "away_goals"})

        # Get the day of week from the match_date column
        df['match_day_of_week'] = (
            pd.to_datetime(df['match_date']).dt.day_name()
        )

        # Remove any duplicate rows
        df = df.drop_duplicates()
        
        return df
        
    except Exception as e:
        logger.error(f"Error cleaning Football-data: {str(e)}")
        raise


def check_football_data(football_data: pd.DataFrame) -> None:
    """
    Validate the Football-data dataframe for data quality and completeness.

    Args:
        football_data (pd.DataFrame): The Football-data dataframe to validate.

    Raises:
        ValueError: If the dataframe fails validation checks.
    """
    
    # Check that the following columns contain no null values: home_club, away_club, match_date, season, league_tier
    required_columns = ['home_club', 'away_club', 'match_date', 'season', 'league_tier']
    for col in required_columns:
        if football_data[col].isnull().any():
            raise ValueError(f"Column {col} contains null values")  
        
    # Club consistency check
    check_clubs_1(matches=football_data, error_stop=True)
    check_clubs_2(matches=football_data, error_stop=False)


def save_football_data(
    football_data: pd.DataFrame,
    output_path: Optional[str] = None
) -> None:
    """
    Save the Football-data dataframe to disk.

    Args:
        football_data (pd.DataFrame): The Football-data dataframe to save.
        output_path (str, optional): Path to save the file. Defaults to
            '../../CleansedData/Interim/football-data.csv'.

    Raises:
        IOError: If there are issues writing the file.
    """
    if output_path is None:
        output_path = Path("../../CleansedData/Interim/football-data.csv")
    else:
        output_path = Path(output_path)
    
    try:
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving cleaned Football-data to {output_path}...")
        football_data.to_csv(output_path, index=False)
        logger.info("Successfully saved cleaned Football-data")
    except IOError as e:
        logger.error(f"Error saving file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error saving file: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Read the data
        football_data = read_football_data()
        
        # Clean the data
        cleaned_football_data = cleanse_football_data(football_data)
        
        # Check the data
        check_football_data(cleaned_football_data)
        
        # Save the data
        save_football_data(cleaned_football_data)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise 