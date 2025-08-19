#!/usr/bin/env python3
"""
Goals vs Age, Foreigners, Value, Size Analysis

This module analyzes the relationship between goals scored and various
team characteristics including age, foreign players, market value, and
team size in the English Premier League.
"""

import logging
import sys
import os
from datetime import datetime
from typing import Optional
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from Utility_code.analysis_utilities import (save_plots, 
                                             wide_to_long_matches)


def setup_logging(
    *,
    log_level: int = logging.INFO,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: The logging level to use (default: INFO)
        log_format: The format string for log messages
    """
    # Create Logs directory if it doesn't exist
    if not os.path.exists("Logs"):
        os.makedirs("Logs")

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Create file handler with timestamp in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"Logs/analysis_{timestamp}.log"

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def main() -> None:
    """
    Main function to orchestrate the analysis workflow.
    """

    # Create key folders if they don't exist
    folders = ["Data", "Plots"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    try:
        setup_logging()
        logging.info("Starting goals vs age, foreigners, value, size analysis")

        # Load data
        matches = pd.read_csv(
            filepath_or_buffer="../../../EPL predictor/2 Data preparation/Data/matches.csv",
            low_memory=False)

        # Load in the foreigners etc. data
        foreigners = pd.read_csv(
            filepath_or_buffer="../../../EPL predictor/1 Data downloads/TransferMarkt-values/Data/transfermarkt.csv",
            low_memory=False).drop(columns=["league tier", "league"])

        # Process data - transform wide to long
        matches = wide_to_long_matches(matches=matches)

        # Merge club_name and season
        goals = matches.merge(foreigners, on=["club_name", "season"], how="left")

        # Save data
        goals.to_csv(path_or_buf="Data/goals_data.csv", index=False)

    except Exception as e:
        logging.error(f"Analysis failed at line {e.__traceback__.tb_lineno}: "
                      f"{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
