#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FootballData.py - Football Match Data Scraper for football-data.co.uk

This module provides functionality to download historical football match data
from football-data.co.uk. It supports downloading data for multiple English
football leagues including Premier League (E0), Championship (E1), League One
(E2), League Two (E3), and Conference (EC).

The script implements polite web scraping by adding random delays between
requests to avoid overwhelming the server. Data is saved in CSV format with
one file per league per season.

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
__summary__ = ("Web scraper for downloading football match data from "
               "football-data.co.uk")

# %%---------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
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
    # This helps avoid being blocked by the server and follows web scraping
    # best practices
    headers = {
        'User-Agent': (
            "Mozilla/5.0 (Linux; Android 13; SM-S901B) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/112.0.0.0 Mobile Safari/537.36"
        )
    }

    # Flag to track if this is the first request (no delay needed for first
    # request)
    first_pass = True

    # Iterate through seasons (1993-2025) and leagues
    # This covers a comprehensive range of historical data
    for year in range(1993, 2026):
        # Process each league tier: Premier League, Championship, League One,
        # League Two, and Conference/National League
        for league in ['E0', 'E1', 'E2', 'E3', 'EC']:
            # Print separator for visual clarity in console output
            print("=" * 51)

            # Implement polite scraping with random delay between 60-120
            # seconds
            # This prevents overwhelming the server and follows ethical
            # scraping practices
            if not first_pass:
                # Generate random sleep time between 60-120 seconds
                sleepy_time = 60 + 60*random.random()
                print(f"Sleeping for {sleepy_time}s.")
                time.sleep(sleepy_time)
            else:
                # Skip delay for the very first request
                first_pass = False

            # Construct the URL for the specific season and league
            # URL format: https://www.football-data.co.uk/mmz4281/2324/E0.csv
            # Convert year range to two-digit format (e.g., 2023 -> "2324")
            y_range = str(year)[2:] + str(year + 1)[2:]
            print(f"Working on season {y_range}")

            # Build the complete URL for the specific league and season
            url = (
                "https://www.football-data.co.uk/mmz4281/"
                f"{y_range}/{league}.csv"
            )
            print(url)

            # Download the CSV data from the constructed URL
            # Use the configured headers to mimic a real browser request
            response = requests.get(url, headers=headers)

            # Check if the request was successful (HTTP 200 status code)
            # If not successful, skip this league/season combination
            if response.status_code != 200:
                print(f"Response code is {response.status_code}")
                continue

            # Process the downloaded data
            # Split the response text into individual lines for processing
            lines = response.text.splitlines()

            # Extract column names from the first line, filtering out empty
            # strings. This handles cases where CSV files might have trailing
            # commas
            column_names = [col for col in lines[0].split(',') if col]

            # Read CSV data using pandas, handling potential formatting issues
            # StringIO converts the text response to a file-like object for
            # pandas. low_memory=False ensures all data is loaded into memory.
            # usecols=column_names ensures we only read the columns that exist
            data_df = pd.read_csv(
                StringIO(response.text),
                low_memory=False,
                usecols=column_names
            )

            # Clean the data by removing empty columns and rows
            # This removes columns that are entirely empty and rows that are
            # entirely empty
            data_df = data_df.dropna(axis=1, how='all').dropna(how='all')

            # Map league code to tier level (EC=5, E0=1, E1=2, etc)
            # This creates a numerical tier system for easier data organization
            level = 5 if league == 'EC' else 1 + int(league[1])

            # Change the date to ISO standard format (YYYY-MM-DD)
            # Try the two-digit year format first, then fall back to four-digit
            # format. This handles different date formats that might exist in
            # the data
            try:
                data_df['match_date'] = pd.to_datetime(
                    data_df['Date'],
                    format="%d/%m/%y"
                ).dt.strftime('%Y-%m-%d')
            except ValueError:
                # If two-digit year format fails, try four-digit year format
                data_df['match_date'] = pd.to_datetime(
                    data_df['Date'],
                    format="%d/%m/%Y"
                ).dt.strftime('%Y-%m-%d')

            # Change the time to 24 hour clock if time column exists
            # Convert time format to standard HH:MM:SS format
            if 'Time' in data_df.columns:
                data_df['match_time'] = pd.to_datetime(
                    data_df['Time'], format="%H:%M"
                ).dt.strftime('%H:%M:%S')
            else:
                # If no time column exists, set a default empty time
                data_df['match_time'] = ''

            # Construct output path and save to CSV
            # Create the full file path using os.path.join for cross-platform
            # compatibility. File naming format: {tier_level}_{year}-{year+1}
            # .csv
            filename = os.path.join(
                "Data-Download",
                f"{str(level)}_{str(year)}-{str(year + 1)}.csv"
            )

            # Save the processed data to CSV file without including the index
            data_df.to_csv(filename, index=False)
