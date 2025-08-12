#!/usr/bin/env python3
"""
Attendance data processing module.

This module provides functions to read match and attendance data,
build combined attendance datasets, and save results to files.
"""

# Standard library imports for file operations, logging, and system utilities
import logging
import os
import sys
import pandas as pd
from pathlib import Path

# Add utilities path to sys.path for imports
# This allows us to import custom analysis utilities from a relative path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Utilities'))

# Import analysis utilities for data validation
from datatests import (
    SeasonData,
    check_clubs_1,
    check_clubs_2
)


# Configure logging for the entire module
# Sets up logging format and level for tracking data processing operations
# Create Logs directory if it doesn't exist
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            filename=logs_dir / "2_attendance.log",
            mode='w'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def read_matches(*,
                 filename: str) -> pd.DataFrame:
    """
    Read matches data from a file.

    Args:
        filename: Path to the matches data file.

    Returns:
        pandas.DataFrame: DataFrame containing matches data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If the file format is invalid.
    """
    try:
        # Log the start of the file reading operation
        logger.info(f"Reading matches data from {filename}")
        
        # Read CSV file with low_memory=False to avoid dtype warnings
        # This is important for large datasets with mixed data types
        matches_df = pd.read_csv(filepath_or_buffer=filename, low_memory=False)
        
        # Log successful completion with record count
        logger.info(f"Successfully read {len(matches_df)} matches")
        return matches_df
        
    except FileNotFoundError as e:
        # Handle case where the specified file doesn't exist
        logger.error(
            f"File not found at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except pd.errors.EmptyDataError as e:
        # Handle case where the CSV file is empty
        logger.error(
            f"Empty file at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except pd.errors.ParserError as e:
        # Handle case where the CSV format is invalid
        logger.error(
            f"Parser error at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during file reading
        logger.error(
            f"Unexpected error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise


def read_attendance(*,
                    filename: str) -> pd.DataFrame:
    """
    Read attendance data from a file.

    Args:
        filename: Path to the attendance data file.

    Returns:
        pandas.DataFrame: DataFrame containing attendance data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If the file format is invalid.
    """
    try:
        # Log the start of the attendance data reading operation
        logger.info(f"Reading attendance data from {filename}")
        
        # Read CSV file with low_memory=False to avoid dtype warnings
        # This ensures consistent data type handling across different file sizes
        attendance_df = pd.read_csv(filepath_or_buffer=filename, low_memory=False)
        
        # Log successful completion with record count
        logger.info(
            f"Successfully read {len(attendance_df)} attendance records"
        )
        return attendance_df
        
    except FileNotFoundError as e:
        # Handle case where the specified attendance file doesn't exist
        logger.error(
            f"File not found at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except pd.errors.EmptyDataError as e:
        # Handle case where the attendance CSV file is empty
        logger.error(
            f"Empty file at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except pd.errors.ParserError as e:
        # Handle case where the attendance CSV format is invalid
        logger.error(
            f"Parser error at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during attendance file reading
        logger.error(
            f"Unexpected error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise


def build_attendance(*,
                     matches: pd.DataFrame,
                     attendance_main: pd.DataFrame,
                     attendance_corrections: pd.DataFrame) -> pd.DataFrame:
    """
    Build combined match attendance dataset.

    Args:
        matches: DataFrame containing matches data.
        attendance_main: DataFrame containing attendance data.
        attendance_secondary: DataFrame containing attendance data.

    Returns:
        pandas.DataFrame: Combined match attendance DataFrame.

    Raises:
        ValueError: If required columns are missing from input DataFrames.
        KeyError: If merge keys are not found in DataFrames.
    """
    try:
        # Log the start of the attendance dataset building process
        logger.info("Building combined attendance dataset")

        # Validate input DataFrames to ensure they contain data
        # This prevents downstream errors from empty datasets
        if matches.empty:
            raise ValueError("Matches DataFrame is empty")
        if attendance_main.empty:
            raise ValueError("Attendance DataFrame is empty")

        # Merge matches and attendance data using left join
        # This preserves all matches and adds attendance data where available
        # The merge keys are season, league_tier, home_club, and away_club
        match_attendance = pd.merge(
            matches,
            attendance_main[['season', 'league_tier', 'home_club',
                            'away_club', 'venue', 'attendance']],
            how='left',
            on=['season', 'league_tier',
                'home_club', 'away_club']
        ).drop_duplicates()

        # Separate matches with attendance data from those without
        # Get the matches that have attendance data (not null)
        attendance = match_attendance[
            match_attendance['attendance'].notnull()
        ].copy()

        # Get the matches that have no attendance data (null values)
        # Select only the columns needed for the corrections merge
        attendance_null = (match_attendance[
            match_attendance['attendance'].isnull()][
                ['season', 'league_tier', 'match_date', 'match_time',
                 'home_goals', 'away_goals', 'home_club', 'away_club',
                 'match_day_of_week']
            ].copy())

        # Merge the null attendance matches with the corrections attendance data
        # This attempts to fill in missing attendance data from corrections
        attendance_null_fixes = pd.merge(
            attendance_null,
            attendance_corrections[['season', 'league_tier', 'home_club',
                                   'away_club', 'venue', 'attendance']],
            how='left',
            on=['season', 'league_tier', 'home_club', 'away_club'])

        # Combine the original attendance data with the corrected data
        match_attendance = pd.concat(objs=[attendance, attendance_null_fixes])

        # Convert attendance to integer type
        match_attendance['attendance'] = match_attendance['attendance'].astype(dtype=float)

        # Then sort the combined dataset for consistent ordering
        match_attendance = match_attendance.sort_values(
            by=['season', 'league_tier', 'match_date', 'home_club']
        )

        # Log successful completion with final record count
        logger.info(
            f"Successfully built dataset with "
            f"{len(match_attendance)} records"
        )
        return match_attendance

    except ValueError as e:
        # Handle validation errors (empty DataFrames, missing columns)
        logger.error(
            f"Value error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise
    except KeyError as e:
        # Handle missing column errors during merge operations
        logger.error(
            f"Key error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during dataset building
        logger.error(
            f"Unexpected error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
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
        # Log the start of the comprehensive data validation process
        logger.info("Starting comprehensive data validation")

        # Check that key columns do not contain null values
        for column in ['season', 'league_tier', 'home_club', 'away_club', 'match_date', 'home_goals', 'away_goals']:
            if data[column].isnull().any():
                raise ValueError(f"{column} column contains null values")

        # Perform club consistency checks using two different validation methods
        # This ensures data integrity from multiple perspectives
        # Check 1: First club validation method
        if not check_clubs_1(matches=data, error_stop=True, logger=logger):
            error_msg = "Club count validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)
        # Check 2: Second club validation method (different approach)
        if not check_clubs_2(matches=data, error_stop=True, logger=logger):
            error_msg = "Club count validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Initialize SeasonData object for reference-based validation
        # This object contains expected values for seasons, leagues, and clubs
        season_data = SeasonData(logger=logger)

        # Validate that each season contains the correct leagues
        # This ensures no seasons have unexpected league tiers
        if not season_data.check_leagues_seasons(matches=data, ignore_tiers=[5]):
            error_msg = "League seasons validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate that each season has the correct number of clubs per league
        # This ensures no leagues have missing or extra teams
        if not season_data.check_leagues_seasons_clubs(matches=data, ignore_tiers=[5]):
            error_msg = "League seasons clubs validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate that each season has the correct number of matches per league
        # This ensures the expected number of games were played
        if not season_data.check_leagues_seasons_matches(matches=data, ignore_tiers=[5]):
            error_msg = "League seasons matches validation failed"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Log successful completion of all validation checks
        logger.info("All data validation checks passed successfully")
        return True

    except Exception as e:
        # Catch any validation errors and provide detailed error information
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
        # Log the start of the data saving operation
        logger.info(f"Saving validated data to {output_path}")

        # Ensure the output directory exists before attempting to save
        # This prevents file writing errors due to missing directories
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(name=output_dir)
            logger.info(f"Created output directory: {output_dir}")

        # Validate data before saving to prevent empty file creation
        # This ensures we don't create files with no meaningful content
        if data.empty:
            error_msg = "Cannot save empty dataset"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Save the validated data to CSV format without index
        # index=False prevents adding an extra index column to the output
        data.to_csv(path_or_buf=output_path, index=False)
        logger.info(
            f"Successfully saved {len(data)} rows to {output_path}"
        )

    except OSError as e:
        # Handle file system errors (permissions, disk space, etc.)
        error_msg = f"Error writing file {output_path}: {str(e)}"
        logger.error(error_msg)
        raise
    except Exception as e:
        # Catch any other unexpected errors during file saving
        error_msg = f"Unexpected error saving data: {str(e)}"
        logger.error(error_msg)
        raise


def save_data(*,
              filename: str,
              dataframe: pd.DataFrame) -> None:
    """
    Save DataFrame to a file.

    Args:
        filename: Path where the file should be saved.
        dataframe: DataFrame to save.

    Raises:
        ValueError: If DataFrame is empty.
        PermissionError: If write permission is denied.
        OSError: If there are file system errors.
    """
    try:
        # Log the start of the data saving operation
        logger.info(f"Saving data to {filename}")

        # Validate that the DataFrame contains data before saving
        # This prevents creating empty files
        if dataframe.empty:
            raise ValueError("DataFrame is empty, nothing to save")

        # Create directory structure if it doesn't exist
        # This uses pathlib for more robust path handling
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save DataFrame to CSV format without index column
        # This creates a clean CSV file without extra index data
        dataframe.to_csv(path_or_buf=filename, index=False)
        logger.info(
            f"Successfully saved {len(dataframe)} records to {filename}"
        )

    except ValueError as e:
        # Handle validation errors (empty DataFrame)
        logger.error(
            f"Value error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise
    except PermissionError as e:
        # Handle permission errors when writing to file
        logger.error(
            f"Permission error at line {e.__traceback__.tb_lineno}: {filename}"
        )
        raise
    except OSError as e:
        # Handle operating system errors (disk space, file system issues)
        logger.error(
            f"OS error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during file saving
        logger.error(
            f"Unexpected error at line {e.__traceback__.tb_lineno}: {str(e)}"
        )
        raise


if __name__ == "__main__":
    # Main execution block - demonstrates the complete data processing pipeline
    try:
        # Step 1: Read all required data files
        # Read the main matches dataset containing game information
        matches = read_matches(
            filename=os.path.join("Data", "matches.csv")
        )

        # Read the main attendance dataset from the external source
        attendance_main = read_attendance(
            filename=os.path.join(
                "..",
                "1 Data downloads",
                "EnglishFootballLeagueTables",
                "Data",
                "englishfootballleaguetables_matches.csv"
            )
        )

        # Read the attendance corrections dataset for filling missing data
        attendance_corrections = read_attendance(
            filename=os.path.join(
                "Corrections",
                "attendance_corrections.csv"
            )
        )

        # Step 2: Build the combined attendance dataset
        # This merges matches with attendance data and applies corrections
        match_attendance = build_attendance(
            matches=matches,
            attendance_main=attendance_main,
            attendance_corrections=attendance_corrections
        )

        # Step 3: Validate the combined dataset
        # This ensures data integrity and consistency
        check_data(data=match_attendance)

        # Step 4: Save the final validated dataset
        # This creates the output file for downstream analysis
        save_data(
            filename="Data/matches_attendance.csv",
            dataframe=match_attendance
        )

        # Print out some check results
        print("Columns in merged data:")
        print(match_attendance.columns)
        print("League tiers in merged data:")
        print(match_attendance['league_tier'].unique())

        # Log successful completion of the entire data processing pipeline
        logger.info("Data processing completed successfully")

    except Exception as e:
        # Handle any errors that occur during the data processing pipeline
        logger.error(f"Data processing failed: {str(e)}")
        raise
