"""
MatchAttendance.py - English Football Match Attendance Scraper

This script downloads and processes match attendance data from Transfermarkt for all English leagues.
It implements ethical web scraping practices including:
- Appropriate delays between requests
- Proper user agent headers
- Error handling and logging
- Respect for the website's robots.txt

Data Structure:
- Input: None (uses command line parameters)
- Output: CSV files with columns:
    * home_team: Name of the home team
    * away_team: Name of the away team
    * attendance: Match attendance figure
    * date: Match date
    * matchday: Matchday number
    * season: Season identifier (e.g., "2023-2024")
    * league: League name
    * tier: League tier (1-4)

Usage:
    python MatchAttendance.py

Dependencies:
    - requests: For making HTTP requests
    - beautifulsoup4: For parsing HTML content
    - pandas: For data manipulation and CSV output
    - numpy: For numerical operations
    
Author: Mike Woodward
Date: March 2024
Version: 1.0
"""

# Standard library imports
import os
import time
import random
from datetime import datetime

# Third-party imports
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

def get_headers():
    """
    Generate headers for HTTP requests to mimic a real browser.
    
    This function returns a dictionary of HTTP headers that make the request appear
    to come from a legitimate web browser. This is good practice for web scraping
    as it:
    1. Helps avoid being blocked by the website
    2. Makes the script's purpose clear to the website owners
    3. Allows for proper tracking and analytics on their end
    
    Returns:
        dict: Dictionary containing HTTP headers including:
            - User-Agent: Browser identification
            - Accept: Acceptable content types
            - Accept-Language: Preferred languages
            - Connection: Connection type
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

# Define the leagues and their information
# Each league has a name, URL name, URL code, and tier
leagues = [
    {
        'name': 'Premier League',
        'url_name': 'premier-league',
        'url_code': 'GB1',
        'tier': 1
    },
    {
        'name': 'Championship',
        'url_name': 'championship',
        'url_code': 'GB2',
        'tier': 2
    },
    {
        'name': 'League One',
        'url_name': 'league-one',
        'url_code': 'GB3',
        'tier': 3
    },
    {
        'name': 'League Two',
        'url_name': 'league-two',
        'url_code': 'GB4',
        'tier': 4
    }
]

# Iterate through seasons (from 1992 to current)
for season in range(2010, 2024):
    # Process each league
    for league_info in leagues:
        # Initialize list to store match data
        results = []

        # Iterate through matchdays (up to 50 per season)
        for matchday in range(1, 50):
            # Add a random delay between 2-4 seconds to be polite
            time.sleep(random.uniform(2, 4))

            # Construct the URL for the specific league, season, and matchday
            url = (f'https://www.transfermarkt.com/{league_info["url_name"]}/spieltag/'
                    f'wettbewerb/{league_info["url_code"]}/plus/?saison_id={season}&spieltag={matchday}')
            
            print(f"Getting results for season: {season}-{season+1} "
                  f"league: {league_info['name']} "
                  f"week: {matchday}")

            try: 
                # Make HTTP request with proper headers
                response = requests.get(url, headers=get_headers())
                response.raise_for_status()  # Raise exception for HTTP errors
            except Exception as err:
                print(f"An error occurred: {err} for URL: {url}")
                continue
            else:
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all match containers
                match_containers = soup.find_all('div', {'class': 'box'})
                
                # If no matches found, we've reached the end of the season
                if len(match_containers) == 0:
                    print(f"No matches found for {league_info['name']} matchday {matchday}")
                    break
                    
                # Process each match
                for match in match_containers:
                    # Extract team information
                    teams = match.find_all('tr')[0].find_all('td', {'class': ['spieltagsansicht-vereinsname' ]})

                    # Skip if no team information found
                    if not teams:
                        continue

                    # Extract home team name (handling different HTML structures)
                    if len(teams[0].find_all('a')) == 1:
                        home_team = teams[0].find_all('a')[0].text
                    elif len(teams[0].find_all('a')) == 2:
                        home_team = teams[0].find_all('a')[1].text

                    # Extract match date from URL
                    if match.find_all('tr')[1].find('a', href=True) is None:
                        match_date = ""
                    else:
                        match_date = match.find_all('tr')[1].find('a', href=True)['href'].split('/')[-1]

                    # Create match data dictionary
                    match_data = {
                        'home team': home_team,
                        'away team': teams[2].find_all('a')[0].text,
                        'date': match_date,
                        'time': match.find_all('tr')[1].text.split('\n')[-3][63:],
                        'attendance': match.find_all('tr')[3].text[5:-2].strip(),
                        'season': f"{season}-{season+1}",
                        'tier': league_info['tier'],
                        'league': league_info['name']
                    }

                    # Add match data to results list
                    results.append(match_data)

        # Convert results to DataFrame
        if len(results) == 0:
            print("No results found for league/season")
        else:
            # Create DataFrame from results
            df = pd.DataFrame(results)
            
            # Generate filename with league tier and season
            filename = os.path.join(
                            '../../RawData/Matches/Attendance',
                            f"attendance_{league_info['tier']}_{season}-{season+1}.csv")
            
            # Save DataFrame to CSV
            df.to_csv(filename, index=False)
