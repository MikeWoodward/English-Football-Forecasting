#!/usr/bin/env python3
"""
Module for downloading, cleaning, and saving match attendance data.
This module handles the processing of match attendance data from multiple sources.
"""

import logging
import pandas as pd
import requests
from pathlib import Path
from typing import Tuple
from io import StringIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
REPO_PATH = "jalapic/engsoccerdata/master/data-raw"
FILES = ["england.csv", "england_nonleague.csv"]


def download_join_csvs() -> pd.DataFrame:
    """
    Downloads CSV files from GitHub and joins them into a single DataFrame.
    Downloads English football match data from the engsoccerdata repository.

    Returns:
        pd.DataFrame: Combined match data from both CSV files.

    Raises:
        requests.RequestException: If there's an error downloading the files.
        pd.errors.EmptyDataError: If the downloaded files are empty.
    """
    try:
        dfs = []
        for file in FILES:
            url = f"{GITHUB_RAW_BASE}/{REPO_PATH}/{file}"
            logger.info(f"Downloading {file} from {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            dfs.append(df)
            logger.info(f"Successfully downloaded and read {file}")

        # Join the dataframes
        attendance5 = pd.concat(dfs, ignore_index=True)
        logger.info("Successfully joined CSV files")
        return attendance5

    except requests.RequestException as e:
        logger.error(f"Error downloading files: {str(e)}")
        raise
    except pd.errors.EmptyDataError as e:
        logger.error(f"Error reading CSV files: {str(e)}")
        raise


def cleanse_attendance5(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and processes the attendance DataFrame.

    Args:
        df (pd.DataFrame): Raw attendance DataFrame to clean.

    Returns:
        pd.DataFrame: Cleaned attendance DataFrame.
    """
    try:
        # Make a copy to avoid modifying the original
        df_clean = df.copy()

        # Remove any duplicate rows
        df_clean = df_clean.drop_duplicates()

        # Sort by date and teams
        df_clean = df_clean.sort_values(['Season', 'tier', 'Date', 'home', 'visitor'])

        # Reset index
        df_clean = df_clean.reset_index(drop=True)

        logger.info("Successfully cleaned attendance data")
        return df_clean

    except Exception as e:
        logger.error(f"Error cleaning data: {str(e)}")
        raise


def save_attendance5(df: pd.DataFrame, output_dir: str = "Data") -> None:
    """
    Saves the cleaned attendance DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): Cleaned attendance DataFrame to save.
        output_dir (str): Directory to save the output file. Defaults to "Data".

    Raises:
        OSError: If there's an error creating the directory or saving the file.
    """
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save to CSV
        output_file = output_path / "engsoccerdata.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Successfully saved attendance data to {output_file}")

    except OSError as e:
        logger.error(f"Error saving file: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Download and join CSVs
        attendance5 = download_join_csvs()

        # Clean the data
        attendance5 = cleanse_attendance5(attendance5)

        # Save the cleaned data
        save_attendance5(attendance5, output_dir="../../RawData/Matches/EngSoccerData")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise 