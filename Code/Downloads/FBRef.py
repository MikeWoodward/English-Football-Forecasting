#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 10:52:08 2025

@author: mikewoodward
"""

# %%---------------------------------------------------------------------------
# Module metadata
# -----------------------------------------------------------------------------
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
from datetime import datetime
import os
import pandas as pd
import random
import requests
import time
import bs4

# %%---------------------------------------------------------------------------
# Function name
# -----------------------------------------------------------------------------


def get_table(*,
              y_range: str,
              league_index: int,
              html: bs4.BeautifulSoup) -> bs4.element.Tag:
    """Find and extract the match schedule table from the FBRef HTML page.
    
    Args:
        y_range: String representing the season range (e.g., "2023-2024")
        league_index: Integer identifier for the league on FBRef
        html: BeautifulSoup object containing the parsed HTML page
    
    Returns:
        bs4.element.Tag: The table containing match data if found, None otherwise
        
    Example:
        table = get_table(y_range="2023-2024", league_index=9, html=parsed_html)
    """
    table_id = """sched_""" + y_range + f"""_{league_index}_1"""
    tables = html.find_all("table", id=table_id)
    if len(tables) != 1:
        return None
    return tables[0]


def get_data(*,
             table: bs4.element.Tag) -> pd.DataFrame:
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
        pd.DataFrame: DataFrame containing the extracted match data with columns for
            date, teams, scores, attendance, and other available statistics
    """
    data = []
    for row in table.find('tbody').find_all('tr'):
        line = {}
        for cell in row.find_all('td'):
            if cell.has_attr("data-stat"):
                text = cell.get_text(strip=True)
                if len(text) == 0:
                    continue
                try:
                    match cell["data-stat"]:
                        case 'score':
                            goals = text.split('–')
                            if len(goals) == 2:
                                try:
                                    line['home_goals'] = int(goals[0])
                                    line['away_goals'] = int(goals[1])
                                except ValueError:
                                    print(f"Invalid score format: {text}")
                                    continue
                        case 'attendance':
                            try:
                                line[cell["data-stat"]] = int(text.replace(',', ''))
                            except ValueError:
                                print(f"Invalid attendance value: {text}")
                                line[cell["data-stat"]] = None
                        case 'date':
                            try:
                                line[cell["data-stat"]] = datetime.strptime(text, "%Y-%m-%d")
                            except ValueError:
                                print(f"Invalid date format: {text}")
                                continue
                        case 'match_report':
                            link = cell.find('a')
                            if link and link.has_attr('href'):
                                line[cell["data-stat"]] = f"https://fbref.com{link['href']}"
                            else:
                                line[cell["data-stat"]] = ""
                        case _:
                            line[cell["data-stat"]] = text
                except Exception as e:
                    print(f"Error processing cell {cell['data-stat']}: {str(e)}")
                    continue
        if len(line) > 0:
            data.append(line)
    return pd.DataFrame(data)


# %%---------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # User-agent for requests
    headers = {'User-Agent':
               """Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"""}
    # League data
    leagues = [
        # {'league_name': """Premier-League""",
        #  'league_tier': 1,
        #  'league_index': 9,
        #  'league_start_year': 1880},
        # {'league_name': """Championship""",
        #  'league_tier':2,
        #  'league_index': 10,
        #  'league_start_year' : 1880},
        # {'league_name': """League-One""",
        #  'league_tier':3,
        #  'league_index': 15,
        #  'league_start_year' : 1880},
        {'league_name': """League-Two""",
         'league_tier':4,
         'league_index': 16,
         'league_start_year' : 1880},
    ]
    for league in leagues:
        for year in range(2023, league['league_start_year'] - 1, -1):   
            
            print("===================================================")
            
            # Pause so we don't get banned
            sleepy_time = 60 + 60*random.random()
            print(f"""Sleeping for {sleepy_time}s.""")
            time.sleep(sleepy_time)
            
            # Build up settings for requests call
            y_range = str(year) + """-""" + str(year + 1)
            print(f"""Working on season {y_range}""")
            url = (f"""https://fbref.com/en/comps/{league['league_index']}/"""
                   + y_range
                   + """/schedule/"""
                   + y_range
                   + f"""-{league['league_name']}-Scores-and-Fixtures""")
            print(url)
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"""Response code is {response.status_code}""")
                continue
                
            # If the response code is good, process the data
            try:
                # Parse the HTML
                html = bs4.BeautifulSoup(response.text, 
                                         features="html.parser")
                # Get the data table
                table = get_table(y_range=y_range,
                                  league_index = league['league_index'],
                                  html=html)
                if table is None:
                    print(f"""No data found for {y_range}""")
                    continue
                # Extract the data from the table
                data_df = get_data(table=table)
                data_df['league_tier'] = league['league_tier']
                # Remove extraneous columns
                data_df = data_df.drop(['away_xg', 'home_xg'], 
                                       errors='ignore', 
                                       axis=1)
                data_df['source'] = "fbref.com"
                
                # Ensure output directory exists
                output_dir = os.path.join("..", "..", "RawData", "Matches", "FBRef")
                os.makedirs(output_dir, exist_ok=True)
                
                # Save to disk
                filename = os.path.join(output_dir,
                    f"{league['league_tier']}_{y_range}.csv")
                data_df.to_csv(filename, index=False)
            except Exception as e:
                print(f"Error processing data for {y_range}: {str(e)}")
                continue
