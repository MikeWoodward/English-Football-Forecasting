#!/usr/bin/env python3
"""
Discipline data processing module.

This module reads match attendance and football discipline data,
merges them on common fields, and performs data validation.
"""

import logging
import os
import sys
import pandas as pd

# Add utilities path to sys.path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Utilities'))

# Import analysis utilities for data validation
from datatests import (
    SeasonData,
    check_clubs_1,
    check_clubs_2
)


def setup_logging() -> None:
    """Set up logging configuration for the module."""
    # Create Logs directory if it doesn't exist
    logs_dir = "Logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logging.info(f"Created Logs directory: {logs_dir}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, '3_discipline.log')),
            logging.StreamHandler()
        ]
    )


def read_match_attendance_data(
    *,
    file_path: str = "Data/matches_attendance.csv"
) -> pd.DataFrame:
    """
    Read the match attendance data from CSV file.

    Args:
        file_path: Path to the match attendance CSV file.

    Returns:
        DataFrame containing match attendance data.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If the file cannot be parsed.
    """
    try:
        logging.info(f"Reading match attendance data from {file_path}")
        attendance_data = pd.read_csv(file_path)
        logging.info(f"Successfully read {len(attendance_data)} rows from "
                    f"match attendance data")
        return attendance_data
    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise
    except pd.errors.EmptyDataError as e:
        logging.error(f"File is empty: {file_path}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise
    except pd.errors.ParserError as e:
        logging.error(f"Error parsing CSV file: {file_path}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise


def read_football_discipline_data(
    *,
    file_path: str = ("../1 Data downloads/FootballData/Data/"
                      "football-data.csv")
) -> pd.DataFrame:
    """
    Read the football discipline data from CSV file.

    Args:
        file_path: Path to the football discipline CSV file.

    Returns:
        DataFrame containing football discipline data.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If the file cannot be parsed.
    """
    try:
        logging.info(f"Reading football discipline data from {file_path}")
        discipline_data = pd.read_csv(file_path)
        logging.info(f"Successfully read {len(discipline_data)} rows from "
                    f"football discipline data")
        return discipline_data
    except FileNotFoundError as e:
        logging.error(f"File not found: {file_path}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise
    except pd.errors.EmptyDataError as e:
        logging.error(f"File is empty: {file_path}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise
    except pd.errors.ParserError as e:
        logging.error(f"Error parsing CSV file: {file_path}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise


def merge_datasets(
    *,
    attendance_data: pd.DataFrame,
    discipline_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge attendance and discipline datasets on common fields.

    Args:
        attendance_data: DataFrame containing match attendance data.
        discipline_data: DataFrame containing football discipline data.

    Returns:
        Merged DataFrame containing both attendance and discipline data.
    """
    logging.info("Merging attendance and discipline datasets")

    # Define merge columns
    merge_columns = ['league_tier', 'season', 'home_club', 'away_club']

    # Check if all merge columns exist in both datasets
    attendance_missing = [col for col in merge_columns
                         if col not in attendance_data.columns]
    discipline_missing = [col for col in merge_columns
                         if col not in discipline_data.columns]

    if attendance_missing:
        logging.error(f"Missing columns in attendance data: {attendance_missing}")
        raise ValueError(f"Missing columns in attendance data: {attendance_missing}")

    if discipline_missing:
        logging.error(f"Missing columns in discipline data: {discipline_missing}")
        raise ValueError(f"Missing columns in discipline data: {discipline_missing}")

    # Add check that merge keys are unique in attandance_data and print out the duplicates
    if attendance_data[merge_columns].duplicated().any():
        logging.error("Merge keys are not unique in attendance data")
        raise ValueError("Merge keys are not unique in attendance data")

    # Add check that merge keys are unique in discipline_data and print out the duplicates
    if discipline_data[merge_columns].duplicated().any():
        logging.error("Merge keys are not unique in discipline data")
        raise ValueError("Merge keys are not unique in discipline data")

    # Perform the merge
    merged_data = pd.merge(
        attendance_data,
        discipline_data,
        on=merge_columns,
        how='left',
        validate='1:1'
    )

    logging.info(f"Successfully merged datasets. Result has "
                f"{len(merged_data)} rows")

    return merged_data


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
        # Log the start of the comprehensive data validation process
        logging.info("Starting comprehensive data validation")

        # Check that key columns do not contain null values
        for column in ['season', 'league_tier', 'home_club', 'away_club',
                      'match_date', 'home_goals', 'away_goals']:
            if data[column].isnull().any():
                raise ValueError(f"{column} column contains null values")

        # Perform club consistency checks using two different validation methods
        # This ensures data integrity from multiple perspectives
        # Check 1: First club validation method
        if not check_clubs_1(matches=data, error_stop=True, logger=logging):
            error_msg = "Club count validation failed"
            logging.error(error_msg)
            raise ValueError(error_msg)
        # Check 2: Second club validation method (different approach)
        if not check_clubs_2(matches=data, error_stop=True, logger=logging):
            error_msg = "Club count validation failed"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Initialize SeasonData object for reference-based validation
        # This object contains expected values for seasons, leagues, and clubs
        season_data = SeasonData(logger=logging)

        # Validate that each season contains the correct leagues
        # This ensures no seasons have unexpected league tiers
        if not season_data.check_leagues_seasons(matches=data, ignore_tiers=[5]):
            error_msg = "League seasons validation failed"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Validate that each season has the correct number of clubs per league
        # This ensures no leagues have missing or extra teams
        if not season_data.check_leagues_seasons_clubs(matches=data,
                                                      ignore_tiers=[5]):
            error_msg = "League seasons clubs validation failed"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Validate that each season has the correct number of matches per league
        # This ensures the expected number of games were played
        if not season_data.check_leagues_seasons_matches(matches=data,
                                                        ignore_tiers=[5]):
            error_msg = "League seasons matches validation failed"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Check that merge keys are unique in data
        merge_columns = ['league_tier', 'season', 'home_club', 'away_club']
        if data[merge_columns].duplicated().any():
            error_data_1 = data[data[merge_columns].duplicated(keep='first')].sort_values(by=merge_columns)
            error_data_2 = data[data[merge_columns].duplicated(keep='last')].sort_values(by=merge_columns)
            error_data = pd.concat([error_data_1, error_data_2]).sort_values(by=merge_columns)
            error_msg = "Merge keys are not unique in data" + "\n" + str(error_data) + "\n"
            logging.error(error_msg)
            raise ValueError(error_msg)

        # Log successful completion of all validation checks
        logging.info("All data validation checks passed successfully")
        return True

    except Exception as e:
        # Catch any validation errors and provide detailed error information
        error_msg = f"Data validation failed: {str(e)}"
        logging.error(error_msg)
        raise


if __name__ == "__main__":
    try:
        # Set up logging
        setup_logging()
        logging.info("Starting discipline data processing")
        
        # Read the datasets
        attendance_data = read_match_attendance_data()
        discipline_data = read_football_discipline_data()
        
        # Merge the datasets
        # Drop duplicate columns from discipline data to avoid conflicts during merge
        merged_data = merge_datasets(
            attendance_data=attendance_data,
            discipline_data=discipline_data.drop(columns=['match_date', 'match_time',
                                                          'home_goals', 'away_goals', 
                                                          'match_day_of_week'])
        )
        
        # Call the check_data function
        validation_result = check_data(data=merged_data)
        
        if validation_result:
            logging.info("Data validation completed successfully")
        else:
            logging.error("Data validation failed")
            raise ValueError("Data validation failed")
        
        # Print out some check results
        print("Columns in merged data:")
        print(merged_data.columns)
        print("League tiers in merged data:")
        print(merged_data['league_tier'].unique())

        # Save the merged data to a CSV file
        # Sort by key fields for consistent output and save to CSV
        merged_data.sort_values(by=['season', 'league_tier', 'home_club', 
                                   'away_club']).to_csv("Data/matches_attendance_discipline.csv", 
                                                        index=False)

        logging.info("Discipline data processing completed successfully")

    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        logging.error(f"Error occurred at line {e.__traceback__.tb_lineno}")
        raise