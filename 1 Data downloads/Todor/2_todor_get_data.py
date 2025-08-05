#!/usr/bin/env python3
"""
Module for processing Todor fixtures data from HTML files.

This module provides functions to read HTML fixture files, process them into
a structured dataframe, and save the processed data to CSV format.
"""

import logging
import pandas as pd
import os
import glob
import re
from bs4 import BeautifulSoup
from typing import List, Dict
import traceback

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, html_folder: str = "HTML") -> List[Dict[str, str]]:
    """
    Read all HTML files from the specified folder in chronological order.

    Args:
        html_folder: Path to the folder containing HTML files.

    Returns:
        List of dictionaries containing 'season' and 'html' keys.

    Raises:
        Exception: If there is an error reading the files.
    """
    try:
        logger.info(
            f"Reading HTML files from folder: {html_folder}"
        )

        # Get all HTML files in the folder
        html_files = glob.glob(os.path.join(html_folder, "*.html"))

        if not html_files:
            logger.error(f"No HTML files found in {html_folder}")
            raise Exception(f"No HTML files found in {html_folder}")

        # Sort files by name to ensure chronological order
        html_files.sort()

        data_list = []

        for file_path in html_files:
            try:
                # Extract season from filename (e.g., "todor_fixtures_1979_1980.html")
                filename = os.path.basename(file_path)
                season_match = re.search(
                    r'todor_fixtures_(\d{4})_(\d{4})',
                    filename
                )

                if season_match:
                    season = f"{season_match.group(1)}-{season_match.group(2)}"
                else:
                    logger.warning(
                        f"Could not extract season from filename: {filename}"
                    )
                    season = "unknown"

                # Read HTML content
                with open(file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                data_list.append({
                    'season': season,
                    'html': html_content
                })

                logger.info(f"Successfully read file: {filename}")

            except Exception as e:
                logger.error(
                    f"Error reading file {file_path}: {str(e)}\n"
                    f"Line number: "
                    f"{traceback.extract_tb(e.__traceback__)[-1].lineno}"
                )
                raise

        logger.info(f"Successfully read {len(data_list)} HTML files")
        return data_list

    except Exception as e:
        logger.error(
            f"Error in read_data: {str(e)}\n"
            f"Line number: "
            f"{traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def process_data(*, data_list: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Process HTML data into a structured matches dataframe.

    Args:
        data_list: List of dictionaries containing 'season' and 'html' keys.

    Returns:
        DataFrame containing processed match data with columns:
        season, date, time, home_team, away_team, home_score, away_score,
        half_time

    Raises:
        Exception: If there is an error processing the data.
    """
    try:
        logger.info("Processing HTML data into matches dataframe")

        matches_data = []

        for data_item in data_list:
            season = data_item['season']

            # Log the season
            logger.info(f"Processing season: {season}")

            html_content = data_item['html']

            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')

            tables = soup.find_all('table')

            match_counter = 0
            logger.info(f"Found {len(tables)} tables")

            for table_index, table in enumerate(tables):

                # Find all table rows
                rows = table.find_all('tr')

                for row_index, row in enumerate(rows):
                    cells = row.find_all('td')

                    # Skip header rows and week separator rows
                    if len(cells) not in [6, 7]:
                        continue

                    # Skip header row where the first cell is "date"
                    if cells[0].text.strip() == "date":
                        continue

                    # Parse the match_date
                    test_date = cells[0].text.strip()
                    # Split the date string if it contains spaces
                    if " " in test_date:
                        test_date = test_date.split(" ")[1]

                    if len(test_date) == 5:
                        day, month = test_date.split(".")
                        # Figure out the year
                        if month in ["08", "09", "10", "11", "12"]:
                            year = season[:4]
                        elif month in ["01", "02", "03", "04", "05", "06"]:
                            year = season[-4:]
                        else:
                            raise ValueError(f"Invalid month: {month}")
                        match_date = f"{year}-{month}-{day}"
                    # Special case for 1997-1998 match
                    elif len(test_date) == 0 and season == "1997-1998":
                        match_date = "1997-08-16"
                    # If the date is 8 characters, it's a date. We know we're above 2000
                    elif len(test_date) == 8:
                        day, month, year = test_date.split(".")
                        match_date = f"20{year}-{month}-{day}"
                    else:
                        raise ValueError(f"Invalid date: {test_date}")

                    # Parse the match_time
                    if cells[1].text.strip() == "--:--":
                        match_time = None
                    else:
                        match_time = cells[1].text.strip()

                    # Parse the score
                    score = cells[3].text.strip()

                    # Some matches have no score because they weren't played
                    if score == "---":
                        continue

                    home_score, away_score = score.split("-")

                    # Get the home and away club names. Remove extraneeous spaces
                    # in the middle of the strings using join.
                    home_club = " ".join(cells[2].text.strip().split())
                    away_club = " ".join(cells[4].text.strip().split())

                    # Add to matches data
                    matches_data.append({
                        'season': season,
                        'league_tier': 5,
                        'match_date': match_date,
                        'match_time': match_time,
                        'home_club': home_club,
                        'away_club': away_club,
                        'home_goals': home_score,
                        'away_goals': away_score,
                    })
                    match_counter += 1

            logger.info(
                f"Processed {match_counter} matches in for season "
                f"{season}"
            )

        # Create DataFrame
        matches_dataframe = pd.DataFrame(matches_data)

        logger.info(f"Successfully processed {len(matches_dataframe)} matches")
        return matches_dataframe

    except Exception as e:
        logger.error(
            f"Error in process_data: {str(e)}\n"
            f"Line number: "
            f"{traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def save_data(*, matches_dataframe: pd.DataFrame,
              output_folder: str = "Data",
              filename: str = "todor_baseline.csv") -> None:
    """
    Save the matches dataframe to a CSV file.

    Args:
        matches_dataframe: DataFrame containing match data.
        output_folder: Folder to save the CSV file in.
        filename: Name of the CSV file to save.

    Raises:
        Exception: If there is an error saving the data.
    """
    try:
        logger.info(f"Saving matches dataframe to {output_folder}/{filename}")

        # Create output directory if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Construct full file path
        file_path = os.path.join(output_folder, filename)

        # Save DataFrame to CSV
        matches_dataframe.to_csv(file_path, index=False)

        logger.info(
            f"Successfully saved {len(matches_dataframe)} matches to "
            f"{file_path}"
        )

    except Exception as e:
        logger.error(
            f"Error in save_data: {str(e)}\n"
            f"Line number: "
            f"{traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


if __name__ == "__main__":
    try:
        logger.info("Starting Todor data processing pipeline")

        # Read data from HTML files
        html_data = read_data()

        # Process data into matches dataframe
        matches_df = process_data(data_list=html_data)

        # Save data to CSV
        save_data(matches_dataframe=matches_df)

        logger.info("Todor data processing pipeline completed successfully")

    except Exception as e:
        logger.error(
            f"Error in main execution: {str(e)}\n"
            f"Line number: "
            f"{traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        ) 