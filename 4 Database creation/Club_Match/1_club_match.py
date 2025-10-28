#!/usr/bin/env python3
"""
Script to build match data from matches_attendance_discipline.csv file.

This script opens and processes the matches_attendance_discipline.csv file
for further analysis and database creation.
"""

import logging
import pandas as pd
import sys


def setup_logging(*, log_level: str = "INFO") -> None:
    """
    Set up logging configuration for the script.

    Args:
        log_level: The logging level to use (default: INFO)
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
    Open and read a CSV file into a pandas DataFrame.

    Args:
        file_path: Path to the CSV file to open

    Returns:
        pandas.DataFrame: The loaded CSV data

    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        pd.errors.EmptyDataError: If the CSV file is empty
        pd.errors.ParserError: If there's an error parsing the CSV
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
    """Main function to execute the match data processing."""
    setup_logging()

    # Define the path to the CSV file
    csv_file_path = (
        "/Users/mikewoodward/Documents/Projects/Python/EPL "
        "predictor/2 Data preparation/Data/"
        "matches_attendance_discipline.csv"
    )

    try:
        # Open the CSV file
        match_data = open_csv_file(file_path=csv_file_path)

        match_data['match_id'] = (
            match_data['match_date'].astype(str) + '-' +
            match_data['home_club'] + '-' +
            match_data['away_club']
        )

        home_match_data = match_data[['match_id', 'home_club', 'home_goals', 'home_red_cards', 'home_yellow_cards', 'home_fouls']].rename(
            columns={'home_club': 'club_name', 'home_goals': 'goals', 'home_red_cards': 'red_cards', 'home_yellow_cards': 'yellow_cards', 'home_fouls': 'fouls'}
        )
        home_match_data['is_home'] = True
        away_match_data = match_data[['match_id', 'away_club', 'away_goals', 'away_red_cards', 'away_yellow_cards', 'away_fouls']].rename(
            columns={'away_club': 'club_name', 'away_goals': 'goals', 'away_red_cards': 'red_cards', 'away_yellow_cards': 'yellow_cards', 'away_fouls': 'fouls'}
        )
        away_match_data['is_home'] = False
        club_match_data = pd.concat([home_match_data, away_match_data]).sort_values(by=['match_id'])

        # Display basic information about the dataset
        logging.info("Dataset Information:")
        logging.info(f"Shape: {match_data.shape}")
        logging.info(f"Columns: {list(match_data.columns)}")

        # Display first few rows
        logging.info("First 5 rows of the dataset:")
        logging.info(f"\n{match_data.head()}")

        # Display data types
        logging.info("Data types:")
        logging.info(f"\n{match_data.dtypes}")

        # Write the match data to a CSV file in the 4 Database creation/Match/Data folder          
        club_match_data.to_csv(
            "/Users/mikewoodward/Documents/Projects/Python/EPL predictor/4 Database creation/Club_Match/Data/club_match.csv",
            index=False
        )


    except Exception as e:
        logging.error(
            f"Error occurred at line {e.__traceback__.tb_lineno}: "
            f"{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
