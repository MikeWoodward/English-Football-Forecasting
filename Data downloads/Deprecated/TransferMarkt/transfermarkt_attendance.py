"""
MatchAttendance.py - English Football Match Attendance Scraper

Downloads and processes match attendance data from Transfermarkt for English 
football leagues. Implements ethical web scraping practices including:
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
import logging

# Third-party imports
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_headers():
    """
    Generate headers for HTTP requests to mimic a real browser.
    
    Returns a dictionary of HTTP headers that make the request appear to come from
    a legitimate web browser. This helps with:
    1. Avoiding being blocked by the website
    2. Making the script's purpose clear
    3. Enabling proper tracking and analytics
    
    Returns:
        dict: Dictionary containing HTTP headers including:
            - User-Agent: Browser identification
            - Accept: Acceptable content types
            - Accept-Language: Preferred languages
            - Connection: Connection type
    """
    return {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/webp,*/*;q=0.8'
        ),
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

# Define league configurations for data collection
# Each league entry contains:
# - name: Display name of the league
# - url_name: URL-friendly name used in web requests
# - url_code: Transfermarkt's internal code for the league
# - tier: League tier (1=Premier League, 2=Championship, etc.)
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
    },
    {
        'name': 'National League',
        'url_name': 'national-league',
        'url_code': 'CNAT',
        'tier': 5
    }
]

# Process data for seasons from 2023 backwards to 1992
# Iterate through each league to collect attendance data
for league_info in leagues:
    # Process each season in reverse order
    for season in range(2023, 1991, -1):
        # Create output filename based on league tier and season
        filename = os.path.join(
            '../../RawData/Matches/Transfermarkt_Attendance',
            f"transfermarktattendance_{league_info['tier']}_{season}-{season+1}.csv"
        )
        
        # Skip if file already exists
        if os.path.exists(filename):
            print(f"File already exists for {league_info['name']} season {season}-{season+1}, skipping...")
            continue
            
        # Store match results for current league and season
        results = []
        time.sleep(random.uniform(3, 6))

        # Process each matchday (maximum of 52 per season)
        for matchday in range(1, 53):
            # Implement polite scraping with delay between requests
            time.sleep(random.uniform(3, 6))

            # Build the URL for the current league, season, and matchday
            base_url = 'https://www.transfermarkt.com'
            url = (
                f'{base_url}/{league_info["url_name"]}/spieltag/wettbewerb/'
                f'{league_info["url_code"]}/plus/?saison_id={season}'
                f'&spieltag={matchday}'
            )
            
            # Log current processing status
            print(
                f"Getting results for season: {season}-{season+1} "
                f"league: {league_info['name']} "
                f"week: {matchday}"
            )

            try: 
                # Fetch webpage content with browser-like headers
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        response = requests.get(url, headers=get_headers())
                        response.raise_for_status()  # Check for HTTP errors
                        break  # If successful, exit the retry loop
                    except Exception as err:
                        retry_count += 1
                        if retry_count == max_retries:
                            print(f"Failed after {max_retries} attempts for URL: {url}. Error: {err}")
                            break
                        print(f"Attempt {retry_count} failed. Waiting 60 seconds before retry... Error: {err}")
                        time.sleep(60)
                
                # If all retries failed, continue to next matchday
                if retry_count == max_retries:
                    continue

            except Exception as err:
                print(f"An unexpected error occurred: {err} for URL: {url}")
                continue
            else:
                print("Successfully fetched webpage")

                # Convert HTML response to BeautifulSoup object for parsing
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all match container elements on the page
                match_containers = soup.find_all('div', {'class': 'box'})
                
                # Check if we've reached the end of available matches
                if len(match_containers) == 0:
                    print(
                        f"No matches found for {league_info['name']} "
                        f"matchday {matchday}"
                    )
                    break
                    
                # Extract data from each match on the page
                for match in match_containers:
                    # Find team name elements within the match container
                    teams = match.find_all('tr')[0].find_all(
                        'td', 
                        {'class': ['spieltagsansicht-vereinsname']}
                    )

                    # Skip matches with missing team information
                    if not teams:
                        continue

                    # Extract home team name, handling different HTML structures
                    # Some teams have one link, others have two
                    if len(teams[0].find_all('a')) == 1:
                        home_team = teams[0].find_all('a')[0].text
                    elif len(teams[0].find_all('a')) == 2:
                        home_team = teams[0].find_all('a')[1].text

                    # Get match date from the URL if available
                    match_url = match.find_all('tr')[1].find('a', href=True)
                    if match_url is None:
                        match_date = ""
                    else:
                        match_date = match_url['href'].split('/')[-1]

                    # Extract matchday number from the page
                    element = match.find_all('tr')[1].find_all('div')
                    if element:
                        match_day_elem = element[0]
                        match_day = match_day_elem.find_all('span')[0].text
                        match_day = match_day.replace(',', '')
                    else:
                        match_day = ""

                    # Parse match time and convert from 12-hour to 24-hour format
                    time_str = match.find_all('tr')[1].text.split('\n')[-3][63:]
                    try:
                        match_time = datetime.strptime(
                            time_str.strip(), 
                            "%I:%M %p"
                        ).strftime("%H:%M")
                    except ValueError as e:
                        logging.warning(
                            f"Failed to parse match time '{time_str}' for "
                            f"{home_team} match on {match_date}. Error: {e}. "
                            "Setting match time to None and continuing."
                        )
                        match_time = None  # Default time for unparseable values

                    # Get match score and split into home/away goals
                    score_elem = match.find_all('tr')[0].find_all(
                        'span', 
                        {'class': ['matchresult']}
                    )[0]
                    score = score_elem.text.split(":")
                    home_goals = score[0]
                    away_goals = score[1]

                    # Clean up attendance
                    attendance = match.find_all('tr')[3].text[5:-2].strip()
                    attendance = attendance.replace('sold out', '').strip()

                    # Compile all match information into a dictionary
                    match_data = {
                        'season': f"{season}-{season+1}",
                        'league_tier': league_info['tier'],
                        'match_date': match_date,
                        'match_day': match_day,
                        'match_time': match_time,
                        'home_club': home_team,
                        'home_goals': home_goals,
                        'away_club': teams[2].find_all('a')[0].text,    
                        'away_goals': away_goals,
                        'attendance': attendance,
                        'league_name': league_info['name']
                    }

                    # Add current match data to results collection
                    results.append(match_data)

        # Process collected results for current league and season
        if len(results) == 0:
            print("No results found for league/season")
        else:
            # Convert collected results to pandas DataFrame
            df = pd.DataFrame(results)
            
            # Save processed data to CSV file
            df.to_csv(filename, index=False)
