"""Module for cleansing English soccer data from engsoccerdata package.

This module provides functions to read, cleanse, and save English soccer data
from the engsoccerdata package. It handles data validation, cleaning of null
values, and ensures data integrity before saving.

The module expects data in CSV format with specific columns including 'Date' and
match-related information. The data is processed and saved in a standardized
format.

Key Features:
- Reads multiple CSV files from the EngSoccerData directory
- Cleanses and standardizes column names
- Validates data integrity
- Handles club name transformations
- Saves processed data in a standardized format
"""

import logging
import pandas as pd
import os
from pathlib import Path
from typing import Optional
from utilities import check_clubs_1, check_clubs_2, transform_club_names

# Configure logging with timestamp, logger name, and message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data() -> pd.DataFrame:
    """Read English soccer data from engsoccerdata CSV files.

    This function reads all CSV files from the EngSoccerData directory and 
    combines them into a single DataFrame. Each file is expected to contain
    match data in a consistent format.

    The function performs the following steps:
    1. Validates the existence of the data directory
    2. Reads each CSV file in the directory
    3. Combines all DataFrames into a single DataFrame
    4. Handles any errors during the reading process

    Returns:
        pd.DataFrame: Combined DataFrame containing all English soccer data.

    Raises:
        FileNotFoundError: If the data directory or CSV files cannot be found.
        pd.errors.EmptyDataError: If any CSV file is empty.
        Exception: For any other errors during file reading.
    """
    # Define the directory containing the raw data files
    data_dir = Path("../../RawData/Matches/EngSoccerData")
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
    # Initialize list to store individual DataFrames from each CSV file
    dfs = []
    
    # Read and process each CSV file in the directory
    for file in data_dir.glob("*.csv"):
        try:
            df = pd.read_csv(file, low_memory=False)
            dfs.append(df)
            logger.info(f"Successfully read {file}")
        except Exception as e:
            logger.error(f"Error reading {file}: {str(e)}")
            raise
            
    # Ensure at least one file was found and processed
    if not dfs:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")
        
    # Combine all DataFrames into a single DataFrame
    return pd.concat(dfs, ignore_index=True)


def cleanse_data(engsoccerdata: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess the English soccer data.

    This function performs data cleaning operations including:
    1. Filtering out lower league tiers (above tier 5)
    2. Standardizing column names
    3. Formatting season data
    4. Removing null values
    5. Transforming club names
    6. Removing unnecessary columns
    7. Checking for data integrity issues
    
    Args:
        engsoccerdata (pd.DataFrame): Raw English soccer data to be cleansed.
            Expected to have a 'Date' column and match-related data.

    Returns:
        pd.DataFrame: Cleansed English soccer data with no null values.

    Raises:
        ValueError: If any rows contain null values after date filtering or if
            duplicate club names are found in the same match.
    """
    # Filter out lower league tiers to focus on top 5 divisions
    engsoccerdata = engsoccerdata[engsoccerdata['tier'] <= 5]

    # Standardize goal column names for consistency
    engsoccerdata = engsoccerdata.rename(
        columns={'hgoal': 'home_goals', 'vgoal': 'away_goals'}
    )

    # Convert season format from single year to year-year+1 format
    # e.g., 2020 becomes 2020-2021
    engsoccerdata['Season'] = engsoccerdata['Season'].apply(
        lambda x: f"{x}-{x+1}"
    )
    engsoccerdata = engsoccerdata.rename(columns={'Season': 'season'})

    # Standardize date column name
    engsoccerdata = engsoccerdata.rename(columns={'Date': 'match_date'})

    # Standardize league tier column name
    engsoccerdata = engsoccerdata.rename(columns={'tier': 'league_tier'})

    # Remove rows with missing dates as they are critical for analysis
    engsoccerdata = engsoccerdata[engsoccerdata['match_date'].notna()]

    # Validate data integrity by checking for null values
    null_rows = engsoccerdata[engsoccerdata.isnull().any(axis=1)]
    if not null_rows.empty:
        logger.warning(f"Rows with null values: {null_rows}")
        raise ValueError("Rows with null values found") 

    # Transform club names to ensure consistency across the dataset
    engsoccerdata = transform_club_names(
        df=engsoccerdata,
        source_name="home",
        target_name="home_club"
    )
    engsoccerdata = transform_club_names(
        df=engsoccerdata,
        source_name="visitor",
        target_name="away_club"
    )

    # Remove redundant columns that can be derived from other data
    cols_to_drop = [
        'FT', 'totgoal', 'goaldif', 'result', 'division'
    ]
    engsoccerdata = engsoccerdata.drop(columns=cols_to_drop)

    # Validate that no team plays against itself
    dupes = engsoccerdata[
        engsoccerdata['home_club'] == engsoccerdata['away_club']
    ]
    if not dupes.empty:
        logger.warning(f"Duplicate rows found: {dupes}")
        raise ValueError("Duplicate rows found")
    
    # Get the day of week from the match_date column
    engsoccerdata['match_day_of_week'] = (
        pd.to_datetime(engsoccerdata['match_date']).dt.day_name()
    )

    return engsoccerdata


def save_data(
    engsoccerdata: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """Save the cleansed English soccer data to disk.

    This function saves the processed DataFrame to a CSV file. If no output path
    is specified, it uses a default path in the CleansedData/Interim directory.
    The function creates any necessary directories in the path.

    The function performs the following steps:
    1. Sets the default output path if none is provided
    2. Creates necessary directories in the output path
    3. Saves the DataFrame to CSV format
    4. Handles any errors during the saving process

    Args:
        engsoccerdata (pd.DataFrame): Cleansed English soccer data to save.
        output_path (Optional[Path]): Path where the data should be saved.
            If None, defaults to '../CleansedData/Interim/engsoccerdata.csv'.

    Raises:
        IOError: If there are any issues creating directories or writing the file.
    """
    if output_path is None:
        output_path = Path("../../CleansedData/Interim/engsoccerdata.csv")
    
    try:
        # Create output directory structure if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save DataFrame to CSV without index column for cleaner output
        engsoccerdata.to_csv(output_path, index=False)
        logger.info(f"Data successfully saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving data to {output_path}: {str(e)}")
        raise IOError(f"Failed to save data: {str(e)}")


if __name__ == "__main__":
    try:
        # Execute the full data processing pipeline
        logger.info("Starting data processing pipeline")
        
        # Step 1: Read the raw data files
        df = read_data()
        logger.info(f"Successfully read {len(df)} rows of data")
        
        # Step 2: Clean and validate the data
        df_cleansed = cleanse_data(df)
        logger.info(
            f"Successfully cleansed data, {len(df_cleansed)} rows remaining"
        )

        # Step 3: Check club consistency across the dataset
        check_clubs_1(matches=df_cleansed, error_stop=True)
        check_clubs_2(matches=df_cleansed, error_stop=False)

        # Step 4: Save the processed data to disk
        save_data(df_cleansed)
        logger.info("Data processing pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise 