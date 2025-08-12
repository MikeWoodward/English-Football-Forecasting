#!/usr/bin/env python3
"""
Module for cleansing Todor football data.

This module provides functions to read, cleanse, and save Todor football data.
It includes functionality for:
- Reading baseline data from CSV files
- Cleansing club names using normalization mapping
- Saving cleansed data to CSV format
"""

import logging
import pandas as pd
import os
import traceback
import sys

# Add parent directory to path to import cleanup utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'DataSourceCleanUp'))

from cleanuputilities import transform_club_names

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, input_file: str = "Data/todor_baseline.csv") -> pd.DataFrame:
    """
    Read Todor baseline data from CSV file into a pandas DataFrame.
    
    Args:
        input_file: Path to the input CSV file containing baseline data.
        
    Returns:
        pd.DataFrame: DataFrame containing the baseline Todor data.
        
    Raises:
        FileNotFoundError: If the input file is not found.
        pd.errors.EmptyDataError: If the input file is empty.
        Exception: If there is an error reading the file.
    """
    try:
        logger.info(f"Reading baseline data from: {input_file}")
        
        # Check if file exists
        if not os.path.exists(input_file):
            error_msg = f"Input file not found: {input_file}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Read CSV file
        baseline_data = pd.read_csv(input_file)
        
        # Validate that data was loaded successfully
        if baseline_data.empty:
            error_msg = f"Input file is empty: {input_file}"
            logger.error(error_msg)
            raise pd.errors.EmptyDataError(error_msg)
        
        logger.info(
            f"Successfully loaded baseline data: {baseline_data.shape[0]} "
            f"rows, {baseline_data.shape[1]} columns"
        )
        
        return baseline_data
        
    except Exception as e:
        # Log detailed error information including line number and traceback
        logger.error(
            f"Error reading baseline data: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def cleanse_data(*, baseline_data: pd.DataFrame) -> pd.DataFrame:
    """
    Cleanse the baseline data by normalizing club names.
    
    This function updates the home_club and away_club columns using the
    transform_club_names function from the cleanup utilities.
    
    Args:
        baseline_data: DataFrame containing the baseline Todor data.
        
    Returns:
        pd.DataFrame: DataFrame with cleansed club names.
        
    Raises:
        Exception: If there is an error during the cleansing process.
    """
    try:
        logger.info("Starting data cleansing process")
        
        # Create a copy to avoid modifying the original data
        cleansed_data = baseline_data.copy()

        # Correct the 18-10-2023 Margate Scarborough match. Change the home_club to Scarborough, and the away club to Margate
        # The home_goals should be 0, and the away_goals should be 1
        selection = (cleansed_data['match_date'] == '2003-10-18') & (cleansed_data['home_club'] == "Margate")
        cleansed_data.loc[selection, 'home_club'] = 'Scarborough'
        cleansed_data.loc[selection, 'away_club'] = 'Margate'
        cleansed_data.loc[selection, 'home_goals'] = 0
        cleansed_data.loc[selection, 'away_goals'] = 1

        # The 2021-2022 season is wrong, so remove it and replace it with some corrections
        cleansed_data = cleansed_data[cleansed_data['season'] != '2021-2022']
        # The 2024-2025 season is wrong, so remove it and replace it with some corrections
        cleansed_data = cleansed_data[cleansed_data['season'] != '2024-2025']

        replacement2021 = pd.read_csv('Corrections/5_2021-2022.csv')
        replacement2024 = pd.read_csv('Corrections/5_2024-2025.csv')
        cleansed_data = pd.concat([cleansed_data, replacement2021, replacement2024])

        # Transform home_club names
        logger.info("Transforming home_club names")
        cleansed_data = transform_club_names(
            df=cleansed_data,
            source_name='home_club',
            target_name='home_club',
            logger=logger
        )
        
        # Transform away_club names
        logger.info("Transforming away_club names")
        cleansed_data = transform_club_names(
            df=cleansed_data,
            source_name='away_club',
            target_name='away_club',
            logger=logger
        )

        # Add a match_day_of_week column from the match_date column, this gives the day as a name, e.g. Saturday
        cleansed_data['match_day_of_week'] = pd.to_datetime(cleansed_data['match_date']).dt.day_name()
        
        # Flag an error if any column (except match_time) has a null value
        for column in cleansed_data.columns:
            if column != 'match_time':
                if cleansed_data[column].isnull().any():
                    logger.error(f"Null values found in column: {column}")
                    raise ValueError(f"Null values found in column: {column}")
                
        # Check that merge keys are unique in data
        merge_columns = ['league_tier', 'season', 'home_club', 'away_club']
        if cleansed_data[merge_columns].duplicated().any():
            error_data_1 = cleansed_data[cleansed_data[merge_columns].duplicated(keep='first')].sort_values(by=merge_columns)
            error_data_2 = cleansed_data[cleansed_data[merge_columns].duplicated(keep='last')].sort_values(by=merge_columns)
            error_data = pd.concat([error_data_1, error_data_2]).sort_values(by=merge_columns)
            error_msg = "Merge keys are not unique in data" + "\n" + str(error_data) + "\n"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Sort the data
        cleansed_data = cleansed_data.sort_values(by=['season', 'match_date', 'home_club'])

        logger.info(
            f"Data cleansing completed successfully. "
            f"Processed {len(cleansed_data)} records"
        )
        
        return cleansed_data
        
    except Exception as e:
        # Log detailed error information including line number and traceback
        logger.error(
            f"Error during data cleansing: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def save_data(*, cleansed_data: pd.DataFrame, 
              output_file: str = "Data/todor_cleansed.csv") -> None:
    """
    Save cleansed data to CSV file.
    
    Args:
        cleansed_data: DataFrame containing the cleansed data to save.
        output_file: Path to the output CSV file.
        
    Raises:
        Exception: If there is an error saving the data.
    """
    try:
        logger.info(f"Saving cleansed data to: {output_file}")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        # Save data to CSV file
        cleansed_data.to_csv(output_file, index=False)
        
        logger.info(
            f"Successfully saved cleansed data: {len(cleansed_data)} rows "
            f"to {output_file}"
        )
        
    except Exception as e:
        # Log detailed error information including line number and traceback
        logger.error(
            f"Error saving cleansed data: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


if __name__ == "__main__":
    try:
        logger.info("Starting Todor data cleansing process")
        
        # Read baseline data
        baseline_data = read_data()
        
        # Cleanse the data
        cleansed_data = cleanse_data(baseline_data=baseline_data)
        
        # Save cleansed data
        save_data(cleansed_data=cleansed_data)
        
        logger.info("Todor data cleansing process completed successfully")
        
    except Exception as e:
        # Log any errors that occur during main execution
        logger.error(
            f"Error in main execution: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        sys.exit(1) 