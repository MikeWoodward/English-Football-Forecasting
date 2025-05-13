"""Module for cleansing English soccer data from engsoccerdata package.

This module provides functions to read, cleanse, and save English soccer data
from the engsoccerdata package. It handles data validation, cleaning of null
values, and ensures data integrity before saving.

The module expects data in CSV format with specific columns including 'Date' and
match-related information. The data is processed and saved in a standardized
format.
"""

import logging
import pandas as pd
import os
from pathlib import Path
from typing import Optional

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
            df = pd.read_csv(file)
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
    1. Removing rows with null dates
    2. Checking for and handling null values in all columns
    
    Args:
        engsoccerdata (pd.DataFrame): Raw English soccer data to be cleansed.
            Expected to have a 'Date' column and match-related data.

    Returns:
        pd.DataFrame: Cleansed English soccer data with no null values.

    Raises:
        ValueError: If any rows contain null values after date filtering.
    """

    # Remove league tiers greater than 5
    engsoccerdata = engsoccerdata[engsoccerdata['tier'] <= 5]

    # Remove any rows where the Date is missing as these are critical
    engsoccerdata = engsoccerdata[engsoccerdata['Date'].notna()]

    # Identify and report any remaining null values in the dataset
    null_rows = engsoccerdata[engsoccerdata.isnull().any(axis=1)]
    if not null_rows.empty:
        logger.warning(f"Rows with null values: {null_rows}")
        raise ValueError("Rows with null values found") 

    # Read in club name normalization file
    club_name_normalization = pd.read_csv(
        "../../CleansedData/Corrections and normalization/"
        "club_name_normalization.csv"
    )
    
    # Report on any clubs (home and away) that are not in the normalization file
    missing_clubs = sorted(set(
        (engsoccerdata[~engsoccerdata['home']
                       .isin(club_name_normalization['club_name'])]
                       ['home'].to_list()) +
        (engsoccerdata[~engsoccerdata['visitor']
                       .isin(club_name_normalization['club_name'])]
                       ['visitor'].to_list())
    ))

    if missing_clubs:
        logger.warning(
            f"Clubs not found in club_name_normalization: {missing_clubs}"
        )
        raise ValueError("Clubs not found in club_name_normalization")         

    # Merge club_name_normalization with df on home_club
    engsoccerdata = pd.merge(
        engsoccerdata,
        club_name_normalization,
        left_on='home',
        right_on='club_name',
        how='left'
    )
    engsoccerdata = engsoccerdata.drop(columns=['home', 'club_name'])
    engsoccerdata = engsoccerdata.rename(columns={'club_name_normalized': 'home'})

    # Merge club_name_normalization with df on away_club
    engsoccerdata = pd.merge(
        engsoccerdata,
        club_name_normalization,
        left_on='away',
        right_on='club_name',
        how='left'
    )
    engsoccerdata = engsoccerdata.drop(columns=['away', 'club_name'])
    engsoccerdata = engsoccerdata.rename(columns={'club_name_normalized': 'away'})

    # Check for name duplication (in the same league)
    dupes = engsoccerdata[engsoccerdata['home_club'] == engsoccerdata['away_club']]
    if not dupes.empty:
        logger.warning(f"Duplicate rows found: {dupes}")
        raise ValueError("Duplicate rows found")
    
    # Check for duplicate names across different leagues in the same season
    dupes

    return engsoccerdata


def save_data(
    engsoccerdata: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """Save the cleansed English soccer data to disk.

    This function saves the processed DataFrame to a CSV file. If no output path
    is specified, it uses a default path in the CleansedData/Interim directory.
    The function creates any necessary directories in the path.

    Args:
        engsoccerdata (pd.DataFrame): Cleansed English soccer data to save.
        output_path (Optional[Path]): Path where the data should be saved.
            If None, defaults to '../CleansedData/Interim/engsoccerdata.csv'.

    Raises:
        IOError: If there are any issues creating directories or writing the file.
    """
    if output_path is None:
        output_path = Path("../CleansedData/Interim/engsoccerdata.csv")
    
    try:
        # Ensure the output directory exists, create if necessary
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the DataFrame to CSV without the index column
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
        
        # Step 3: Save the processed data
        save_data(df_cleansed)
        logger.info("Data processing pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise 