#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FootballData.py - Football Match Data Scraper for football-data.co.uk

This module provides functionality to download historical football match data from 
football-data.co.uk. It supports downloading data for multiple English football leagues
including Premier League (E0), Championship (E1), League One (E2), League Two (E3),
and Conference (EC).

The script implements polite web scraping by adding random delays between requests
to avoid overwhelming the server. Data is saved in CSV format with one file per 
league per season.

League codes:
    E0 - Premier League (Tier 1)
    E1 - Championship (Tier 2)
    E2 - League One (Tier 3)
    E3 - League Two (Tier 4)
    EC - Conference/National League (Tier 5)

Example Usage:
    $ python FootballData.py

The script will:
1. Download data for all leagues from 2013-2024
2. Clean and process the data
3. Save CSV files in ../../../RawData/Matches/Football-data/
   with naming format: {tier_level}_{year}-{year+1}.csv

Requirements:
    Python >= 3.10
    pandas
    requests

Created on Fri Feb 28 10:52:08 2025
@author: mikewoodward
"""

# %%---------------------------------------------------------------------------
# Module metadata
# -----------------------------------------------------------------------------
__author__ = "mikewoodward"
__license__ = "MIT"
__summary__ = "Web scraper for downloading football match data from football-data.co.uk"

# %%---------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
from datetime import datetime
from io import StringIO
import os
import pandas as pd
import random
import requests
import time

# %%---------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Configure request headers with a user agent to identify our scraper
    headers = {'User-Agent':
               """Mozilla/5.0 (Linux; Android 13; SM-S901B) """
               """AppleWebKit/537.36 (KHTML, like Gecko) """
               """Chrome/112.0.0.0 Mobile Safari/537.36"""}
    
    # Iterate through seasons (1993-2024) and leagues
    for year in range(1993, 2024):
        for league in ['E0', 'E1', 'E2', 'E3', 'EC']:          
            print("===================================================")
            
            # Implement polite scraping with random delay between 60-120 seconds
            sleepy_time = 60 + 60*random.random()
            print(f"""Sleeping for {sleepy_time}s.""")
            time.sleep(sleepy_time)            

            # Construct the URL for the specific season and league
            # URL format: https://www.football-data.co.uk/mmz4281/2324/E0.csv
            y_range = str(year)[2:] + str(year + 1)[2:]
            print(f"""Working on season {y_range}""")
            url = ("""https://www.football-data.co.uk/mmz4281/"""
                   + y_range
                   + "/"
                   + league
                   + """.csv""")
            print(url)

            # Download the CSV data
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print(f"""Response code is {response.status_code}""")
                continue
                
            # Process the downloaded data
            lines = response.text.splitlines()
            # Extract column names, filtering out empty strings
            column_names = [col for col in lines[0].split(',') if col]
            
            # Read CSV data using pandas, handling potential formatting issues
            data_df = pd.read_csv(StringIO(response.text),
                                  low_memory=False,
                                  usecols=column_names)
            
            # Clean the data by removing empty columns and rows
            data_df = data_df.dropna(axis=1, how='all').dropna(how='all')
            
            # Add data source information
            data_df['source'] = "football-data.co.uk"
            
            # Map league code to tier level (EC=5, E0=1, E1=2, etc)
            level = 5 if league=='EC' else 1 + int(league[1])
            
            # Construct output path and save to CSV
            filename = os.path.join(
                "..",
                "..",
                "RawData",
                "Matches",
                "Football-data",
                f"{str(level)}_{str(year)}-{str(year + 1)}.csv")
            data_df.to_csv(filename, 
                           index=False)
