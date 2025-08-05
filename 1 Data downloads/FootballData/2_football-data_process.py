#!/usr/bin/env python3
"""
Module for cleaning and processing Football-data data.

This module provides functions to read, clean, validate, and save Football-data.
"""

# Import required libraries for data processing and file operations
import logging
import pandas as pd
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to import DataSourceCleanUp
sys.path.append(str(Path(__file__).parent.parent))
from DataSourceCleanUp.cleanuputilities import transform_club_names

# Configure logging with timestamp, module name, and log level for better
# debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_football_data() -> pd.DataFrame:
    """
    Read and concatenate all Football-data from CSV files in the RawData
    directory.

    Returns:
        pd.DataFrame: The concatenated Football-data from all CSV files.

    Raises:
        FileNotFoundError: If the RawData directory cannot be found.
        pd.errors.EmptyDataError: If any of the CSV files are empty.
    """
    try:
        # Log the start of the data reading process
        logger.info("Reading Football-data from CSV files...")

        # Define the directory path where raw data files are stored
        data_dir = Path("Data-Download")

        # Check if the data directory exists before proceeding
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory not found: {data_dir}")

        # Initialize list to store all dataframes from CSV files
        dfs = []

        # Iterate through all CSV files in the directory
        for csv_file in data_dir.glob(pattern="*.csv"):
            logger.info(f"Reading {csv_file.name}...")

            # Read each CSV file into a pandas dataframe
            df = pd.read_csv(filepath_or_buffer=csv_file)

            # Extract league tier from first character of filename (e.g., "1" for tier 1)
            league_tier = csv_file.stem[0]
            df['league_tier'] = league_tier

            # Extract season from characters 3 to 11 of filename (e.g., "1993-1994")
            season = csv_file.stem[2:11]
            df['season'] = season

            # Add the processed dataframe to our collection
            dfs.append(df)

        # Check if any CSV files were found and processed
        if not dfs:
            raise FileNotFoundError("No CSV files found in the directory")

        # Combine all individual dataframes into one large dataframe
        football_data = pd.concat(
            objs=dfs,
            ignore_index=True
        )

        # Log the total number of rows processed and return the combined data
        logger.info(f"Successfully read {len(football_data)} rows of Football-data")
        return football_data
        
    except FileNotFoundError as e:
        # Handle case where data directory or files don't exist
        logger.error(f"Error accessing files: {str(object=e)}")
        raise
    except pd.errors.EmptyDataError:
        # Handle case where CSV files are empty or corrupted
        logger.error("One or more CSV files are empty")
        raise
    except Exception as e:
        # Handle any other unexpected errors during data reading
        logger.error(f"Unexpected error reading Football-data: {str(object=e)}")
        raise


def cleanse_football_data(*, football_data: pd.DataFrame) -> pd.DataFrame:
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
        # Log the start of the data cleaning process
        logger.info("Cleaning Football-data...")
        
        # Create a copy of the input dataframe to avoid modifying the original data
        df = football_data.copy()

        # Remove all non-English teams from the dataframe
        foreign_clubs = ["Anderlecht", "Antwerp", "Club Brugge", "Dender",
                         "Oud-Heverlee Leuven", "RAAL La Louviere", "St Truiden",
                         "Waregem"]
        df = df[~df['HomeTeam'].isin(foreign_clubs)]
        df = df[~df['AwayTeam'].isin(foreign_clubs)]
        
        # Define the specific columns we want to keep in our cleaned dataset
        columns_to_keep = [
            'HomeTeam', 'AwayTeam', 'match_date', 'match_time',
            'season', 'league_tier', 'FTHG', 'FTAG', 'HY', 'AY', 'HR', 'AR',
            "HF", "AF"
        ]
        
        # Validate that all required columns exist in the dataframe
        missing_columns = [col for col in columns_to_keep if col not in df.columns]
        if missing_columns:
            raise KeyError(
                f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Filter the dataframe to keep only the columns we need
        df = df[columns_to_keep]

        # Rename columns to more descriptive names: FTHG -> home_goals, FTAG -> away_goals
        df = df.rename(columns={"HomeTeam": "home_club",
                                "AwayTeam": "away_club",
                                "FTHG": "home_goals", 
                                "FTAG": "away_goals",
                                "HY": "home_yellow_cards",
                                "AY": "away_yellow_cards",
                                "HR": "home_red_cards",
                                "AR": "away_red_cards",
                                "HF": "home_fouls",
                                "AF": "away_fouls"})

        # Extract day of the week from the match_date column for analysis
        df['match_day_of_week'] = (
            pd.to_datetime(arg=df['match_date']).dt.day_name()
        )

        # Convert goal columns to integer type for proper numerical operations
        df['home_goals'] = df['home_goals'].astype(dtype=int)
        df['away_goals'] = df['away_goals'].astype(dtype=int)
        
        # Correct the home_club name and away_club name
        df = transform_club_names(
            df=df,
            source_name="home_club",
            target_name="home_club",
            logger=logging
        )
        df = transform_club_names(
            df=df,
            source_name="away_club",
            target_name="away_club",
            logger=logging
        )

        # Remove any duplicate rows to ensure data integrity
        df = df.drop_duplicates()
        
        return df
        
    except Exception as e:
        # Handle any errors that occur during the data cleaning process
        logger.error(f"Error cleaning Football-data: {str(object=e)}")
        raise


def check_football_data(*, football_data: pd.DataFrame) -> None:
    """
    Validate the Football-data dataframe for data quality and completeness.

    Args:
        football_data (pd.DataFrame): The Football-data dataframe to validate.

    Raises:
        ValueError: If the dataframe fails validation checks.
    """
    
    # Define the critical columns that must not contain null values for data quality
    required_columns = ['home_club', 'away_club', 'match_date', 'season', 'league_tier']
    
    # Check each required column for null values and raise error if any are found
    for col in required_columns:
        if football_data[col].isnull().any(axis=None):
            raise ValueError(f"Column {col} contains null values")  


def save_football_data(
    *, 
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
    # Set default output path if none provided
    if output_path is None:
        output_path = Path("Data/football-data.csv")
    else:
        output_path = Path(output_path)
    
    try:
        # Create the output directory structure if it doesn't already exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Log the save operation and write the dataframe to CSV
        logger.info(f"Saving cleaned Football-data to {output_path}...")
        football_data.to_csv(path_or_buf=output_path, index=False)
        logger.info("Successfully saved cleaned Football-data")
    except IOError as e:
        # Handle file system errors (permissions, disk space, etc.)
        logger.error(f"Error saving file: {str(object=e)}")
        raise
    except Exception as e:
        # Handle any other unexpected errors during file saving
        logger.error(f"Unexpected error saving file: {str(object=e)}")
        raise


if __name__ == "__main__":
    try:
        # Step 1: Read raw football data from CSV files
        football_data = read_football_data()
        
        # Step 2: Clean and process the raw data
        cleaned_football_data = cleanse_football_data(
            football_data=football_data
        )
        
        # Step 3: Validate the cleaned data for quality and completeness
        check_football_data(football_data=cleaned_football_data)

        # Sort data
        cleaned_football_data = cleaned_football_data.sort_values(by=['season', 'league_tier', 'match_date', 'home_club'])
        
        # Step 4: Save the processed data to disk
        save_football_data(football_data=cleaned_football_data)
        
    except Exception as e:
        # Handle any errors that occur during the entire data processing pipeline
        logger.error(f"An error occurred: {str(object=e)}")
        raise 
