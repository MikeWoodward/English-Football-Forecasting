#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 10:52:08 2025

@author: mikewoodward
"""

# %%---------------------------------------------------------------------------
# Module metadata
# -----------------------------------------------------------------------------
import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
from typing import Optional, List, Dict, Any, Union
import traceback
import time
import sys
import random
import os
import logging
from datetime import datetime
import argparse
__author__ = "mikewoodward"
__license__ = "MIT"
__summary__ = "Web scraper for downloading football match data from FBRef.com"

"""
This module provides functionality to scrape football match data from FBRef.com.
It can download historical match results and schedules for various English football leagues
including Premier League, Championship, League One, and League Two.

Requirements:
    Python >= 3.10 (needed for match statement syntax)
    Required packages: requests, beautifulsoup4, pandas

The scraper respects rate limits by implementing random delays between requests to avoid
being blocked by the website. Data is saved in CSV format with one file per league per season.

Features:
- Scrapes match schedules, scores, and additional metadata
- Supports multiple leagues and historical seasons
- Implements polite scraping with random delays
- Saves data in a structured CSV format
- Handles missing data and network errors gracefully

Example usage:
    Run the script directly to download League Two data:
    $ python FBRef.py
"""

# %%---------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
# Standard library imports


# Third-party imports

# Type aliases
DataFrameType = pd.DataFrame
BeautifulSoupType = BeautifulSoup
RequestsResponseType = requests.Response
MatchDataType = Dict[str, Union[str, int, datetime, None]]


def setup_logging(debug_mode: bool = False) -> None:
    """Configure logging with both file and console handlers.

    Args:
        debug_mode: If True, sets logging level to DEBUG, otherwise INFO
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'fbref_scraper_{timestamp}.log')

    # Set up logging configuration
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

    # Log initial debug status
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Debug mode: {debug_mode}")
    if debug_mode:
        logger.debug("Debug logging enabled")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='FBRef.com football match data scraper'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with verbose logging'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2023,
        help='Start year for scraping (default: 2023)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        help='End year for scraping (default: league start year)'
    )
    parser.add_argument(
        '--league',
        choices=['Premier-League', 'Championship', 'League-One', 'League-Two'],
        help='Specific league to scrape (default: all leagues)'
    )
    return parser.parse_args()

# %%---------------------------------------------------------------------------
# Function name
# -----------------------------------------------------------------------------


def get_table(*,
              y_range: str,
              league_index: int,
              html: BeautifulSoupType) -> Optional[Tag]:
    """Find and extract the match schedule table from the FBRef HTML page.

    Args:
        y_range: String representing the season range (e.g., "2023-2024")
        league_index: Integer identifier for the league on FBRef
        html: BeautifulSoup object containing the parsed HTML page

    Returns:
        Optional[Tag]: The table containing match data if found, None otherwise

    Example:
        table = get_table(y_range="2023-2024", league_index=9, html=parsed_html)
    """
    table_id = f"sched_{y_range}_{league_index}_1"
    tables = html.find_all("table", id=table_id)
    if len(tables) != 1:
        logger.warning(
            f"Expected 1 table with id {table_id}, found {len(tables)}")
        return None
    return tables[0]


def get_data(*,
             table: Tag) -> DataFrameType:
    """Extract match data from an HTML table and convert it to a pandas DataFrame.

    This function parses the HTML table row by row, extracting various match statistics
    and metadata including:
    - Match date
    - Teams (home and away)
    - Scores
    - Attendance
    - Match report URLs

    Args:
        table: BeautifulSoup Tag object containing the match data table

    Returns:
        DataFrameType: DataFrame containing the extracted match data with columns for
            date, teams, scores, attendance, and other available statistics
    """
    data: List[MatchDataType] = []
    tbody = table.find('tbody')
    if not tbody:
        logger.error("No tbody found in table")
        return pd.DataFrame()

    for row in tbody.find_all('tr'):
        line: MatchDataType = {}
        for cell in row.find_all('td'):
            if not cell.has_attr("data-stat"):
                continue

            stat_name = cell["data-stat"]
            text = cell.get_text(strip=True)
            if not text:
                continue

            try:
                match stat_name:
                    case 'score':
                        goals = text.split('–')
                        if len(goals) == 2:
                            try:
                                line['home_goals'] = int(goals[0])
                                line['away_goals'] = int(goals[1])
                            except ValueError:
                                logger.warning(f"Invalid score format: {text}")
                                continue
                    case 'attendance':
                        try:
                            line[stat_name] = int(text.replace(',', ''))
                        except ValueError:
                            logger.warning(f"Invalid attendance value: {text}")
                            line[stat_name] = None
                    case 'dayofweek':
                        try:
                            line[stat_name] = text
                        except ValueError:
                            logger.warning(f"Invalid date format: {text}")
                            continue
                    case 'date':
                        try:
                            line[stat_name] = datetime.strptime(
                                text, "%Y-%m-%d")
                        except ValueError:
                            logger.warning(f"Invalid date format: {text}")
                            continue
                    case 'match_report':
                        link = cell.find('a')
                        if link and link.has_attr('href'):
                            line[stat_name] = f"https://fbref.com{link['href']}"
                        else:
                            line[stat_name] = ""
                    case _:
                        line[stat_name] = text
            except Exception as e:
                logger.error(f"Error processing cell {stat_name}: {str(e)}")
                continue

        # Only add line if not empty and match not cancelled
        if (not ('notes' in line and line['notes'] == 'Match Cancelled')
                and line != {}):
            data.append(line)

    return pd.DataFrame(data)


# %%---------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)

    try:
        # User-agent for requests
        headers = {
            'User-Agent': (
                "Mozilla/5.0 (Linux; Android 13; SM-S901B) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/112.0.0.0 Mobile Safari/537.36"
            )
        }

        # League data
        leagues = [
            {
                'league_name': "Premier-League",
                'league_tier': 1,
                'league_index': 9,
                'league_start_year': 1888
            },
            {
                'league_name': "Championship",
                'league_tier': 2,
                'league_index': 10,
                'league_start_year': 2014
            },
            {
                'league_name': "League-One",
                'league_tier': 3,
                'league_index': 15,
                'league_start_year': 2014
            },
            {
                'league_name': "League-Two",
                'league_tier': 4,
                'league_index': 16,
                'league_start_year': 2014
            },
        ]

        # Filter leagues if specified
        if args.league:
            leagues = [l for l in leagues if l['league_name'] == args.league]
            if not leagues:
                raise ValueError(f"League {args.league} not found")

        logger.info("Starting FBRef data scraping")

        for league in leagues:
            logger.info(f"Processing league: {league['league_name']}")

            # Determine end year
            end_year = args.end_year or league['league_start_year']

            for year in range(args.start_year,
                              end_year - 1,
                              -1):
                # Build season range string
                y_range = f"{year}-{year + 1}"
                logger.info(f"Working on season {y_range}")

                # Pause so we don't get banned
                sleepy_time = 30 + 30*random.random()
                logger.info(f"Sleeping for {sleepy_time:.2f}s")
                time.sleep(sleepy_time)

                # Build URL
                url = (
                    f"https://fbref.com/en/comps/{league['league_index']}/"
                    f"{y_range}/schedule/{y_range}-{league['league_name']}"
                    "-Scores-and-Fixtures"
                )
                logger.debug(f"Requesting URL: {url}")

                try:
                    # Make request with timeout
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()

                    # Parse the HTML
                    html = BeautifulSoup(response.text, features="html.parser")

                    # Get the data table
                    table = get_table(
                        y_range=y_range,
                        league_index=league['league_index'],
                        html=html
                    )
                    if table is None:
                        logger.warning(f"No data found for {y_range}")
                        continue

                    # Extract the data from the table
                    data_df = get_data(table=table)
                    if data_df.empty:
                        logger.warning(f"No data extracted for {y_range}")
                        continue

                    # Add metadata
                    data_df['league_tier'] = league['league_tier']
                    data_df['source'] = "fbref.com"

                    # Remove extraneous columns
                    data_df = data_df.drop(
                        ['away_xg', 'home_xg'],
                        errors='ignore',
                        axis=1
                    )

                    # Ensure output directory exists
                    output_dir = os.path.join(
                        "..", "..", "RawData", "Matches", "FBRef")
                    os.makedirs(output_dir, exist_ok=True)

                    # Save to disk
                    filename = os.path.join(
                        output_dir,
                        f"{league['league_tier']}_{y_range}.csv"
                    )
                    data_df.to_csv(filename, index=False)
                    logger.info(f"Saved data to {filename}")

                except requests.Timeout:
                    logger.error(f"Request timed out for {url}")
                    continue
                except requests.RequestException as e:
                    logger.error(f"Request failed for {url}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(
                        f"Error processing data for {y_range}: {str(e)}\n"
                        f"{''.join(traceback.format_exc())}"
                    )
                    if args.debug:
                        raise  # Re-raise exception in debug mode
                    continue

        logger.info("FBRef data scraping completed")

    except Exception as e:
        logger.critical(
            f"Critical error occurred: {str(e)}\n"
            f"{''.join(traceback.format_exc())}"
        )
        sys.exit(1)

    sys.exit(0)
