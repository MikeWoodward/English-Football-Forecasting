#!/usr/bin/env python3
"""
Module for scraping National League match data from Todor website.

This module provides functions to retrieve, process, and save National League
match data from the Todor website. It handles data from seasons 1979-80 to
1997-98, extracting match details including dates, teams, and scores.
"""

import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional
import os
import time
import traceback

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retrieve_matches(year: int) -> pd.DataFrame:
    """
    Retrieve National League match data for a specific season.

    Args:
        year (str): The year to retrieve data for.

    Returns:
        pd.DataFrame: DataFrame containing match data with columns for date,
            home team, away team, score, etc.

    Raises:
        Exception: If there is an error retrieving the data.
    """
    try:
        # Initialize empty list to store match data
        matches = []
        logger.info(f"Retrieving match data for year: {year}")

        # Construct URL for the specific season
        # Note: URL uses year+1 as seasons span two calendar years
        season_url = (
            f"http://todor66.com/football/England/Conference/{year+1}.html"
        )
        response = requests.get(season_url)
        
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            html = BeautifulSoup(response.text, features="html.parser")
            
            # Find all tables in the HTML and log their count
            tables = html.find_all('table')

            # Process each table to extract match data
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) == 0:
                    continue
                # Verify table structure by checking header row
                cols = rows[0].find_all('td')
                if len(cols) != 6:
                    continue
                if cols[0].text.strip() != 'date' or cols[1].text.strip() != 'time':
                    continue
                
                # Process each row in the table
                for row in rows[1:]:
                    cols = row.find_all('td')
                    if len(cols) != 6:
                        continue
                    # Extract and process date
                    # Handle dates that span two calendar years
                    dm = cols[0].text.strip()
                    if dm == '':
                        date = None
                    else:
                        day, month = dm.split('.')
                        # Determine which year the date belongs to
                        # Months > 6 are in the first year, <= 6 in the second
                        if int(month)> 6:
                            date = str(year) + '-' + month + '-' + day
                        else:
                            date = str(year + 1) + '-' + month + '-' + day   
                    # Extract team names and scores
                    home_club = cols[2].text.strip()
                    away_club = cols[4].text.strip()
                    score_parts = cols[3].text.strip().split('-')
                    home_goals = score_parts[0]
                    away_goals = score_parts[1]

                    # Create match record and add to list
                    matches.append({
                        'season': str(year) + "-" + str(year + 1),
                        'league_tier': 5,  # National League is tier 5
                        'date': date,
                        'home_club': home_club, 
                        'away_club': away_club,
                        'home_goals': home_goals,
                        'away_goals': away_goals
                    })
 
        else:
            logger.error(
                f"Failed to retrieve data. Status code: {response.status_code}"
            )
            
        return pd.DataFrame(matches)
    except Exception as e:
        # Log detailed error information including line number and traceback
        logger.error(
            f"Error retrieving match data: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def get_data() -> pd.DataFrame:
    """
    Retrieve all available National League match data.

    Returns:
        pd.DataFrame: DataFrame containing all available match data.

    Raises:
        Exception: If there is an error retrieving the data.
    """
    try:
        logger.info("Retrieving all National League match data")
        
        # Initialize list to store matches from all seasons
        all_matches = []
        
        # Process each season from 1979-80 to 1997-98
        for year in range(1979, 1999):
            logger.info(f"Processing season {year}")
            season_matches = retrieve_matches(year)
            all_matches.append(season_matches)
            # Add delay between requests to be respectful to the server
            time.sleep(10)
        
        # Combine all matches and remove any duplicates
        matches = pd.concat(all_matches, ignore_index=True).drop_duplicates()
        logger.info(f"Total matches retrieved: {len(matches)}")
        return matches
    except Exception as e:
        # Log detailed error information
        logger.error(
            f"Error getting data: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def save_data(data: pd.DataFrame, filename: Optional[str] = None) -> None:
    """
    Save National League match data to a file.

    Args:
        data (pd.DataFrame): The match data to save.
        filename (Optional[str]): The name of the file to save to.
            If None, a default name will be used.

    Raises:
        Exception: If there is an error saving the data.
    """
    try:
        # Use default filename if none provided
        if filename is None:
            filename = "todor.csv"
        
        # Create directory structure for saving data
        save_dir = os.path.join("..", "..", "RawData", "Matches", "todor")
        os.makedirs(save_dir, exist_ok=True)
        
        # Construct full file path and save data
        file_path = os.path.join(save_dir, filename)
        
        logger.info(f"Saving data to {file_path}")
        data.to_csv(file_path, index=False)
        logger.info("Data saved successfully")
    except Exception as e:
        # Log detailed error information
        logger.error(
            f"Error saving data: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


if __name__ == "__main__":
    try:
        # Main execution: retrieve and save all match data
        data = get_data()
        save_data(data)
    except Exception as e:
        # Log any errors that occur during main execution
        logger.error(
            f"Error in main execution: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        ) 