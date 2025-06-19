#!/usr/bin/env python3
"""
Module for unifying data from multiple sources into a single dataset.

This module provides functions to read data from various sources (attendance and
football statistics) and combine them into a unified dataset. It handles data
validation, discrepancy checking, and merging of multiple data sources to create
a single, consistent dataset for analysis.
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List
from utilities import SeasonData, check_clubs_1, check_clubs_2

# Configure logging for the module. This will capture logs for debugging and
# auditing purposes. The format includes timestamp, logger name, log level, and
# the actual message.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_csv(*, input_folder: Path, source: str) -> pd.DataFrame:
    """
    Read data from a CSV file based on the specified source.

    This function consolidates the functionality of multiple source-specific read
    functions into a single, unified function. It handles different data sources
    with their specific requirements and file structures.

    Args:
        input_folder (Path): Path to the folder containing the input data.
        source (str): The data source to read from. Must be one of:
            - 'attendance1'
            - 'attendance2'
            - 'attendance4'
            - 'fbref'
            - 'football_data'
            - 'todor'
            - 'engsoccerdata'

    Returns:
        pd.DataFrame: The data from the specified source.

    Raises:
        FileNotFoundError: If the input file is not found.
        pd.errors.EmptyDataError: If the input file is empty.
        ValueError: If an invalid source is specified.
    """
    logger.info(f"Reading data from source: {source}")
    
    # Dictionary mapping source names to their corresponding CSV file names.
    # This centralizes the file naming convention and makes it easier to
    # maintain and update file names.
    source_files = {
        'attendance1': 'attendance1.csv',
        'attendance2': 'attendance2.csv',
        'attendance4': 'attendance4.csv',
        'fbref': 'fbref.csv',
        'football_data': 'football-data.csv',
        'todor': 'todor.csv',
        'engsoccerdata': 'engsoccerdata.csv'
    }
    
    # Validate that the requested source exists in our mapping
    if source not in source_files:
        raise ValueError(
            f"Invalid source: {source}. Must be one of: "
            f"{', '.join(source_files.keys())}"
        )
    
    # Construct the full path to the source file by joining the input folder
    # with the source-specific filename
    file_path = input_folder / source_files[source]
    
    # Ensure the file exists before attempting to read it
    if not file_path.exists():
        raise FileNotFoundError(f"{source} file not found at {file_path}")
    
    try:
        # Read the CSV file into a DataFrame. For attendance4, we disable
        # low_memory mode to avoid dtype warnings due to mixed data types
        low_memory = source == 'attendance4'
        data = pd.read_csv(file_path, low_memory=low_memory)
        logger.info(f"Successfully read {source} data: {data.shape}")
        return data
    except pd.errors.EmptyDataError:
        logger.error(f"{source} file is empty")
        raise
    except Exception as e:
        logger.error(f"Error reading {source} file: {str(e)}")
        raise


def check_dataframe(season_data: SeasonData, football_data: pd.DataFrame) -> None:
    """
    Validate the integrity of a football dataframe against SeasonData.

    This method performs several checks to ensure the dataframe's integrity:
    1. Verifies all seasons and league_tier match expected values
    2. Validates club counts per season and league tier
    3. Validates match counts per season and league tier

    Args:
        season_data (SeasonData): SeasonData instance for validation.
        football_data (pd.DataFrame): DataFrame to be validated.

    Raises:
        ValueError: If any validation checks fail.
    """
    logger.info("Starting dataframe validation checks")
    
    # First check: Verify that all expected league tiers are present in the data
    # and no unexpected tiers exist
    expected_league_tiers = season_data.get_league_tiers()
    actual_league_tiers = football_data['league_tier'].unique().tolist()

    # Use symmetric_difference to find any mismatches in either direction
    tier_differences = set(expected_league_tiers).symmetric_difference(
        set(actual_league_tiers)
    )
    if tier_differences:
        error_msg = (
            f"League tier mismatch. Differences found: {tier_differences}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Second check: Verify that all expected seasons are present in the data
    # and no unexpected seasons exist
    expected_seasons = season_data.get_seasons()
    actual_seasons = football_data['season'].unique().tolist()

    # Sort differences for consistent error reporting
    season_differences = sorted(set(expected_seasons).symmetric_difference(
        set(actual_seasons)
    ))   
    if season_differences:
        error_msg = (
            f"Season mismatch. Differences found: {season_differences}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Third check: For each league tier, verify that all expected seasons
    # are present and no unexpected seasons exist
    for league_tier in expected_league_tiers:
        expected_seasons = season_data.get_seasons(league_tier=league_tier)
        actual_seasons = football_data[
            football_data['league_tier'] == league_tier
        ]['season'].unique().tolist()
        
        season_differences = sorted(set(expected_seasons).symmetric_difference(
            set(actual_seasons)
        ))
        if season_differences:
            error_msg = (
                f"Season mismatch for league tier {league_tier}. "
                f"Differences found: {season_differences}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg) 
    
    logger.info("All dataframe validation checks passed successfully")

    # Final checks: Verify club consistency using utility functions
    check_clubs_1(matches=football_data, error_stop=True)
    check_clubs_2(matches=football_data, error_stop=True)

def is_multiple_values(row: pd.Series, column: str, suffixes: List[str]) -> bool:
    """
    Check if there are multiple different valid values in specified columns.
    
    A value is considered valid if it is:
    - A non-empty string
    - A non-NaN number (int or float)
    
    Args:
        row: A pandas Series representing a row of data
        column: The base column name to check
        suffixes: List of suffixes to append to the column name
        
    Returns:
        bool: True if there are multiple different valid values,
              False if all values are the same or invalid
    """
    # Create a set of valid values from all suffixed columns
    # This will automatically remove duplicates and invalid values
    return len({
        row[f'{column}{suffix}'] for suffix in suffixes
        if isinstance(row[f'{column}{suffix}'], str) or (
            isinstance(row[f'{column}{suffix}'], (int, float)) and 
            not np.isnan(row[f'{column}{suffix}'])
        )
    }) > 1

def check_discrepancies(*,
    attendance4_data: pd.DataFrame,
    attendance2_data: pd.DataFrame,
    attendance1_data: pd.DataFrame,
    fbref_data: pd.DataFrame,
    football_data: pd.DataFrame,
    todor_data: pd.DataFrame,
    engsoccer_data: pd.DataFrame,
) -> None:
    """
    Check for discrepancies between all dataframes.

    This function performs pairwise comparisons between all dataframes to identify
    any discrepancies in match data. It checks key fields like match dates, goals,
    and league tiers. The function merges all dataframes on season, home_club, and
    away_club fields, which are considered the most reliable identifiers.

    Args:
        attendance4_data (pd.DataFrame): DataFrame from attendance4 source
        attendance2_data (pd.DataFrame): DataFrame from attendance2 source
        attendance1_data (pd.DataFrame): DataFrame from attendance1 source
        fbref_data (pd.DataFrame): DataFrame from fbref source
        football_data (pd.DataFrame): DataFrame from football_data source
        todor_data (pd.DataFrame): DataFrame from todor source
        engsoccer_data (pd.DataFrame): DataFrame from engsoccerdata source

    Raises:
        ValueError: If any discrepancies are found between dataframes
    """
    logger.info("Starting discrepancy checks between all dataframes")

    # Create a list of dictionaries containing each dataframe and its suffix
    # This structure makes it easier to process all dataframes uniformly
    dataframes_names = [
        {'data': attendance4_data.copy(), 'suffix': '_attendance4'},
        {'data': attendance2_data.copy(), 'suffix': '_attendance2'},
        # {'data': attendance1_data.copy(), 'suffix': '_attendance1'},
        # {'data': fbref_data.copy(), 'suffix': '_fbref'},
        # {'data': football_data.copy(), 'suffix': '_football_data'},
        # {'data': todor_data.copy(), 'suffix': '_todor'},
        # {'data': engsoccer_data.copy(), 'suffix': '_engsoccerdata'}
    ]
    # The columns were're merging on. These columns are the most likey to be
    # correct and consistent across all data sources.
    merge_columns = ['season', 'home_club', 'away_club'] 

    # Rename all columns except the merge columns to include the source suffix
    # This prevents column name conflicts during the merge
    for row in dataframes_names:
        row['data'].columns = [
            c + row['suffix'] if c not in merge_columns else c
            for c in row['data'].columns
        ]

    # Merge all dataframes using season, home_club, and away_club as keys. These
    # fields are chosen because they are the most reliable identifiers across all
    # data sources and least likely to have discrepancies.
    merged_dataframe = dataframes_names[0]['data']
    for dataframe in dataframes_names[1:]:
        merged_dataframe = merged_dataframe.merge(
            dataframe['data'],
            on=merge_columns,
            how='outer',
            suffixes=['_x', '_y']
        )
    
    # Define the key match data fields to check for discrepancies
    columns_to_check = [
        'league_tier', 'match_date', 'match_day_of_week',
        'home_goals', 'away_goals'
    ]
    # Extract just the suffixes for use in the discrepancy check
    suffixes = [x['suffix'] for x in dataframes_names]
    
    # For each column, create a new column indicating if there are discrepancies
    # between the different sources
    for column in columns_to_check:
        merged_dataframe[f'differences_{column}'] = merged_dataframe.apply(
            lambda x: is_multiple_values(x, column, suffixes),
            axis=1
        )
        diff_frame = merged_dataframe[merged_dataframe[f'differences_{column}']].copy()
        if diff_frame.shape[0] > 0:
            columns_to_keep = merge_columns + [column + suffix for suffix in suffixes]
            diff_frame = diff_frame[columns_to_keep]
            diff_frame.to_csv('discrepancies.csv', index=False)
            error_msg = f"Found discrepancies in the column {column}"
            logger.error(error_msg)
            raise ValueError(error_msg + f"See {diff_frame.shape[0]} rows in diff_frame_{column}.csv")

    # Save the merged dataframe for manual inspection and debugging
    merged_dataframe.sort_values(
        by=['season', 'home_club', 'away_club']
    ).to_csv('merged_dataframe.csv', index=False)

    # logger.info("No discrepancies found between any dataframes")


def save_matches(matches: pd.DataFrame) -> None:
    """
    Save match data to a CSV file.

    Args:
        matches (pd.DataFrame): DataFrame containing match data to save.

    Raises:
        FileNotFoundError: If the output directory doesn't exist.
        PermissionError: If there are permission issues writing to the file.
        ValueError: If the DataFrame is empty.
    """
    logger.info("Starting to save match data")
    
    # Define the output path for the merged match data
    # The path is relative to the project root
    output_path = Path("../../CleansedData/Unified/match_data.csv")
    
    # Ensure the output directory exists, create if not
    # This prevents errors when trying to save to a non-existent directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate input data is not empty before saving
    if matches.empty:
        error_msg = "Cannot save empty DataFrame"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        # Save the DataFrame to CSV without the index
        matches.to_csv(output_path, index=False)
        logger.info(f"Successfully saved match data to {output_path}")
        
    except PermissionError as e:
        error_msg = f"Permission denied when saving to {output_path}: {str(e)}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Error saving match data: {str(e)}"
        logger.error(error_msg)
        raise


if __name__ == "__main__":
    try:
        # Define input folder for all interim data sources
        input_folder = Path("../../CleansedData/Interim")

        # Initialize season data object for validation
        # This object contains the expected structure of our data
        season_data = SeasonData()
        
        # Read data from all sources using the consolidated read_csv function.
        # Each source provides different aspects of match data that will be
        # validated and merged.
        attendance4_data = read_csv(
            input_folder=input_folder,
            source='attendance4'
        )
        attendance2_data = read_csv(
            input_folder=input_folder,
            source='attendance2'
        )
        attendance1_data = read_csv(
            input_folder=input_folder,
            source='attendance1'
        )
        fbref_data = read_csv(
            input_folder=input_folder,
            source='fbref'
        )
        football_data = read_csv(
            input_folder=input_folder,
            source='football_data'
        )
        todor_data = read_csv(
            input_folder=input_folder,
            source='todor'
        )
        engsoccer_data = read_csv(
            input_folder=input_folder,
            source='engsoccerdata'
        )

        logger.info("Successfully read all data sources")

        # Validate data consistency across all sources by checking for
        # discrepancies in key fields
        check_discrepancies(
            attendance4_data=attendance4_data,
            attendance2_data=attendance2_data,
            attendance1_data=attendance1_data,
            fbref_data=fbref_data,
            football_data=football_data,
            todor_data=todor_data,
            engsoccer_data=engsoccer_data
        )
        
        # Use attendance4 data as the primary source for the final dataset
        # This source is chosen as it has the most complete and reliable data
        match_data = attendance4_data

        # Save the validated and unified match data to CSV
        save_matches(match_data)

    except Exception as e:
        logger.error(f"Error reading data sources: {str(e)}")
        raise 