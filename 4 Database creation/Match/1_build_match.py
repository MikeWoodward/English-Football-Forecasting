#!/usr/bin/env python3
"""
Match Data Builder for EPL Predictor Database.

This script processes raw match data from the
matches_attendance_discipline.csv file to create a clean, normalized match
dataset suitable for database storage and analysis. The script performs the
following key operations:

1. Loads match data from CSV file with comprehensive error handling
2. Generates unique match_id by combining date, home club, and away club
3. Creates league_id by combining league tier and season year
4. Filters and sorts data for optimal database storage
5. Exports processed data to match.csv for database import

Input: matches_attendance_discipline.csv (raw match data)
Output: match.csv (processed match data for database)

Author: Data Science Team
Date: 2024
"""

import logging
import pandas as pd
import sys


def setup_logging(*, log_level: str = "INFO") -> None:
    """
    Configure logging for the match data processing script.

    Sets up dual logging output to both file and console with timestamped
    messages. Log file is saved as 'match_processing.log' in the current
    directory.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR,
                  CRITICAL). Defaults to INFO.

    Example:
        setup_logging(log_level="DEBUG")  # Enable debug logging
        setup_logging()  # Use default INFO level
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('match_processing.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def open_csv_file(*, file_path: str) -> pd.DataFrame:
    """
    Safely load CSV file into pandas DataFrame with comprehensive error
    handling.

    This function provides robust CSV file loading with detailed error
    reporting and logging. It handles common CSV loading issues including
    missing files, empty files, and parsing errors.

    Args:
        file_path: Absolute or relative path to the CSV file to load

    Returns:
        pandas.DataFrame: The loaded CSV data with all columns and rows

    Raises:
        FileNotFoundError: If the specified CSV file doesn't exist
        pd.errors.EmptyDataError: If the CSV file exists but contains no data
        pd.errors.ParserError: If the CSV file has formatting issues

    Example:
        df = open_csv_file(file_path="/path/to/data.csv")
        print(f"Loaded {len(df)} rows")
    """
    try:
        logging.info(f"Opening CSV file: {file_path}")
        dataframe = pd.read_csv(file_path, low_memory=False)
        logging.info(
            f"Successfully loaded CSV file with {len(dataframe)} rows "
            f"and {len(dataframe.columns)} columns"
        )
        return dataframe

    except FileNotFoundError as e:
        logging.error(
            f"File not found at line {e.__traceback__.tb_lineno}: "
            f"{file_path}"
        )
        raise

    except pd.errors.EmptyDataError as e:
        logging.error(
            f"Empty CSV file at line {e.__traceback__.tb_lineno}: "
            f"{file_path}"
        )
        raise

    except pd.errors.ParserError as e:
        logging.error(
            f"Error parsing CSV at line {e.__traceback__.tb_lineno}: "
            f"{file_path} - {str(e)}"
        )
        raise


def main() -> None:
    """
    Execute the complete match data processing pipeline.

    This function orchestrates the entire data processing workflow:
    1. Sets up logging for the session
    2. Loads raw match data from CSV
    3. Performs data transformations and cleaning
    4. Generates derived fields (match_id, league_id)
    5. Filters and sorts the final dataset
    6. Exports processed data to CSV file

    The processed data is saved to the Match/Data directory for database
    import and further analysis.
    """
    # Initialize logging system for this processing session
    setup_logging()

    # Define the path to the source CSV file containing raw match data
    # This file contains match details, attendance, and discipline information
    csv_file_path = (
        "/Users/mikewoodward/Documents/Projects/Python/EPL "
        "predictor/2 Data preparation/Data/"
        "matches_attendance_discipline.csv"
    )

    try:
        # ================================================================
        # DATA LOADING SECTION
        # ================================================================

        # Load raw match data from CSV file with error handling
        match_data = open_csv_file(file_path=csv_file_path)

        # ================================================================
        # DATA TRANSFORMATION SECTION
        # ================================================================

        # Generate unique match identifier by combining date and team names
        # Format: YYYY-MM-DD-HomeTeam-AwayTeam (e.g., 2023-08-12-Arsenal-
        # Chelsea)
        match_data['match_id'] = (
            match_data['match_date'].astype(str) + '-' +
            match_data['home_club'] + '-' +
            match_data['away_club']
        )

        # Create league identifier by combining tier and season year
        # Formula: (league_tier * 10000) + season_year
        # Example: Premier League (tier 1) in 2023 = 12023
        match_data['league_id'] = (
            match_data['league_tier'] * 10000 +
            match_data['season'].str.split('-').str[0].astype(int)
        )

        # ================================================================
        # DATA FILTERING AND SORTING SECTION
        # ================================================================

        # Select only essential columns for the final dataset
        # Sort by league_id first, then by match_date for chronological order
        match_data = match_data[[
            'league_id', 'match_id', 'match_date', 'attendance'
        ]].sort_values(by=['league_id', 'match_date'])

        # ================================================================
        # DATA VALIDATION AND REPORTING SECTION
        # ================================================================

        # Log comprehensive dataset information for validation
        logging.info("Processed Dataset Summary:")
        logging.info(f"Shape: {match_data.shape} (rows, columns)")
        logging.info(f"Columns: {list(match_data.columns)}")
        logging.info(f"Date range: {match_data['match_date'].min()} to "
                     f"{match_data['match_date'].max()}")
        logging.info(f"Unique leagues: {match_data['league_id'].nunique()}")
        logging.info(f"Total matches: {len(match_data)}")

        # Display sample data for manual verification
        logging.info("Sample data (first 5 rows):")
        logging.info(f"\n{match_data.head()}")

        # Log data types to ensure proper formatting
        logging.info("Column data types:")
        logging.info(f"\n{match_data.dtypes}")

        # ================================================================
        # DATA EXPORT SECTION
        # ================================================================
        # Export processed match data to CSV file for database import
        # File is saved in the Match/Data directory for database creation
        output_path = (
            "/Users/mikewoodward/Documents/Projects/Python/EPL predictor/"
            "4 Database creation/Match/Data/match.csv"
        )
        match_data.to_csv(output_path, index=False)
        logging.info(f"Successfully exported {len(match_data)} matches to "
                     f"{output_path}")

    except Exception as e:
        # ================================================================
        # ERROR HANDLING SECTION
        # ================================================================

        # Log detailed error information including line number and context
        logging.error(
            f"Critical error occurred at line {e.__traceback__.tb_lineno}: "
            f"{str(e)}"
        )
        logging.error(
            "Processing terminated due to error. Check logs for details."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
