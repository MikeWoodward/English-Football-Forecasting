#!/usr/bin/env python3
"""
Module for downloading fixtures tables from Todor website.

This module provides functions to retrieve and save fixtures table data
from the Todor website. It handles downloading table data for specific
seasons and saving them to the appropriate directory structure.
"""

import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import Optional
import os
import traceback

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_table_v1(*, tables: list[BeautifulSoup]) -> pd.DataFrame:
    """
    Retrieve fixtures table for a specific year from Todor website.
    """
    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) == 0:
            continue
        columns = [col.text.strip() for col in rows[0].find_all('td')]
        if columns == ["date", "time", "team 1", "score", "team 2", "HT"]:
            return table
        if columns == ['date', 'time', 'Home', 'score', 'Away', 'HT', '']:
            return table
        
    return None
        
def get_table_v2(*, tables: list[BeautifulSoup]) -> pd.DataFrame:
    """
    Retrieve fixtures table for a specific year from Todor website.
    """
    html = ""
    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) <2:
            continue

        rows = table.find_all('tr')
        if len(rows) == 0:
            continue

        # Remove any tables that are playoff tables
        if len(rows) > 2:
            columns =rows[2].find_all("td")
            if len(columns) == 1:
                continue

        columns = [col.text.strip() for col in rows[0].find_all('td')]
        if columns == ['date', 'time', 'team 1 ____________', 'score', 'team 2 ____________', 'HT', '']:
            html += str(table)      
    return html
        
def get_table(*, year: int) -> pd.DataFrame:
    """
    Retrieve fixtures table for a specific year from Todor website.

    Args:
        year: The year to retrieve table data for.

    Returns:
        pd.DataFrame: DataFrame containing the fixtures table data.

    Raises:
        Exception: If there is an error retrieving the table data.
    """
    try:
        logger.info(f"Retrieving fixtures table for year: {year}")
        
        # Construct URL for the specific season
        # Note: URL uses year+1 as seasons span two calendar years
        if year < 2023:
            season_url = (
                f"http://todor66.com/football/England/Conference/{year+1}.html"
            )
        else:
            season_url = (
                f"http://todor66.com/football/England/Conference/{year}-{year+1}.html"
            )
        
        response = requests.get(season_url)
        
        if response.status_code != 200:
            logger.error(
                f"Failed to retrieve data for URL {season_url}. Status code: {response.status_code}"
            )
            raise Exception(f"HTTP {response.status_code}: {response.reason}")
        
        # Parse the HTML content using BeautifulSoup
        html = BeautifulSoup(response.text, features="html.parser")
        
        # Find all tables in the HTML, reverse to make proessing easier
        tables = html.find_all('table')[::-1]
        
        if year in [1979, 
                    1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
                    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
                    2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007,
                    2017, 2018]:
            return get_table_v1(tables=tables)
        else:
            return get_table_v2(tables=tables)

        
    except Exception as e:
        # Log detailed error information including line number and traceback
        logger.error(
            f"Error retrieving fixtures table: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


def save_table(*, table: str, year: int, 
               filename: Optional[str] = None) -> None:
    """
    Save fixtures table data to a file in the specified directory.

    Args:
        data: The fixtures table data to save.
        year: The year the data corresponds to.
        filename: The name of the file to save to. If None, a default
            name will be generated based on the year.

    Raises:
        Exception: If there is an error saving the data.
    """
    try:
        # Use default filename if none provided
        if filename is None:
            filename = f"todor_fixtures_{year}_{year+1}.html"
        
        # Create directory structure for saving data
        save_dir = os.path.join("HTML")
        os.makedirs(save_dir, exist_ok=True)
        
        # Construct full file path and save data
        file_path = os.path.join(save_dir, filename)
        
        # save table to file
        with open(file_path, 'w') as f:
            f.write(str(table))
        
    except Exception as e:
        # Log detailed error information
        logger.error(
            f"Error saving fixtures table: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise


if __name__ == "__main__":
    try:
        for year in range(1979, 2025):
            logger.info(f"Starting fixtures table download for year {year}")
        
            # Get the fixtures table
            fixtures_table = get_table(year=year)
            
            # Save the fixtures table
            save_table(table=fixtures_table, year=year)
            
            logger.info("Fixtures table download completed successfully")
        
    except Exception as e:
        # Log any errors that occur during main execution
        logger.error(
            f"Error in main execution: {str(e)}\n"
            f"Line number: {traceback.extract_tb(e.__traceback__)[-1].lineno}\n"
            f"Traceback: {traceback.format_exc()}"
        ) 