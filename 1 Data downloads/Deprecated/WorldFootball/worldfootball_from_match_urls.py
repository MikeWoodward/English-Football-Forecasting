"""Match Attendance Data Scraper.

This script scrapes attendance data from football match web pages and processes it into a structured format.
It reads match URLs from a text file, extracts relevant match information including attendance figures,
and saves the data to CSV files with periodic checkpoints.

The script handles:
- Reading match URLs from an input file
- Web scraping of match details (teams, scores, dates, times, attendance)
- Data extraction using BeautifulSoup
- Error handling and progress tracking
- Saving data to CSV files with checkpoints

Typical usage:
    python match_attendance4.py

Requirements:
    - requests: For making HTTP requests
    - beautifulsoup4: For HTML parsing
    - pandas: For data manipulation and CSV handling

The script expects a match_urls.txt file in the specified input directory and
creates CSV output in the specified output directory.

Author: [Your Name]
Date: [Current Date]
Version: 4.0
"""

# Standard library imports for basic functionality
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Third-party imports for data processing and web scraping
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Define file paths using Path for cross-platform compatibility
# Path to the input file containing match URLs
match_urls_path = Path('../../RawData/Matches/WorldFootball_MatchURLs/worldfootball_match_urls.txt')

# Attempt to read match URLs from the input file
try:
    with open(match_urls_path, 'r', encoding='utf-8') as file:
        match_list_urls = file.read().splitlines()
except FileNotFoundError:
    print(f"Error: Could not find file at {match_urls_path}")
    match_list_urls = []

# Initialize list to store match data dictionaries
match_list = []

# Create output directory for storing CSV files
# Create intermediate directories if needed with parents=True
output_dir = Path('../../RawData/Matches/WorldFootball_Attendance')
output_dir.mkdir(parents=True, exist_ok=True)


def save_progress(data: list, step_number: int) -> None:
    """Save the current match data to a CSV checkpoint file.

    Creates a checkpoint CSV file containing all processed match data up to the
    current point. Useful for data recovery in case of script interruption.

    Args:
        data: List of dictionaries containing match information.
        step_number: Current processing step number used in checkpoint filename.

    Returns:
        None. Saves data to a CSV file and prints confirmation message.
    """
    # Convert list of dictionaries to DataFrame and save as CSV
    df = pd.DataFrame(data)
    checkpoint_file = f'worldfootball_attendance_checkpoint_{step_number}.csv'
    output_file = output_dir / checkpoint_file
    df.to_csv(output_file, index=False)
    print(f"\nCheckpoint saved: {output_file}")


# Main processing loop - iterate through each match URL
for i, url in enumerate(match_list_urls[::-1]):
    try:
        # Add delay between requests to prevent server overload
        if i > 0:  # Skip delay for first request
            time.sleep(2)

        # Extract season and league information from URL
        base_url = 'https://www.worldfootball.net/report/'
        dummy = url.split(base_url)[1]
        # Split on the first occurrence of YYYY-YYYY pattern
        parts = re.split(r'(\d{4}-\d{4})', dummy, maxsplit=1)
        season = parts[1]

        # Extract and format league name
        test_league = parts[0].replace('-', ' ').strip().title()

        # Determine league tier based on league name
        if 'Premier League' in test_league:
            league_tier = 1
        elif 'Championship' in test_league:
            league_tier = 2
        elif 'League One' in test_league:
            league_tier = 3        
        elif 'League Two' in test_league:
            league_tier = 4   
        elif 'National League' in test_league:
            league_tier = 5

        # Fetch and parse webpage content
        print(f"Processing URL {i+1} of {len(match_list_urls)}: {url}")
        response = requests.get(url)
        match_page = response.text
        soup = BeautifulSoup(match_page, 'html.parser')
        
        # Find all tables containing match information
        tables = soup.find_all('table', class_='standard_tabelle')
        
        # Validate that tables were found
        if not tables:
            print(
                f"Warning: No tables found with class 'standard_tabelle' "
                f"for URL: {url}"
            )
            continue
        
        # Process main match details from the first table
        first_table = tables[0]
        rows = first_table.find_all('tr')
        
        # Validate table structure
        if not rows:
            print(f"Warning: No rows found in the table for URL: {url}")
            continue
            
        # Get team names and match timing from first row
        first_row = rows[0]
        columns = first_row.find_all('th')
        
        # Ensure row has enough columns
        if len(columns) < 3:
            print(f"Warning: Not enough columns in first row for URL: {url}")
            continue
        
        # Extract home team name from link
        home_team_link = columns[0].find('a')
        if not home_team_link:
            print(f"Warning: No home team link found for URL: {url}")
            continue
        home_team_name = home_team_link.text.strip()
        
        # Extract and format match date and time
        if (br_tag := columns[1].find('br')):
            # Handle cases where date and time are separated by <br> tag
            match_date = (
                br_tag.previous_sibling.strip() if br_tag.previous_sibling else ''
            )
            match_time = (
                br_tag.next_sibling.strip() if br_tag.next_sibling else ''
            )
            # Clean up time format by removing 'Clock' text
            match_time = match_time.replace('Clock', '').strip()
        else:
            match_date = columns[1].text.strip()
            match_time = ''
        
        # Process date
        splitter = match_date.split(',')
        match_day = splitter[0]
        match_date = splitter[1].replace('.', '').strip()
        # Convert the date from this format '8 September 1888'to YYYY-MM-DD
        match_date = (
            datetime.strptime(match_date, '%d %B %Y')
            .strftime('%Y-%m-%d')
        )
        
        # Extract away team name from link
        away_team_link = columns[2].find('a')
        if not away_team_link:
            print(f"Warning: No away team link found for URL: {url}")
            continue
        away_team_name = away_team_link.text.strip()
        
        # Extract match score from the second row
        if len(rows) < 2:
            print(f"Warning: No second row found for URL: {url}")
            continue
            
        second_row_cells = rows[1].find_all('td')
        if len(second_row_cells) < 2:
            print(f"Warning: Not enough columns in second row for URL: {url}")
            continue
        
        # Parse the score into home and away goals (format: "home:away")
        match_score = second_row_cells[1].text.strip().split(":")
        match_home_score = match_score[0]
        match_away_score = match_score[1]
        
        # Extract attendance from the last table by finding the attendance row
        rows = tables[-1].find_all('tr')
        match_attendance = None
        for row in rows:
            image = row.find('img')
            if image and image['title'] == 'Attendance':
                # Remove thousand separators from attendance number
                match_attendance = row.text.strip().replace(".", "")
                break
        
        # Extract venue from the last table by finding the stadium row
        rows = tables[-1].find_all('tr')
        venue = None
        for row in rows:
            image = row.find('img')
            if image and image['title'] == 'stadium':
                # Extract venue name without additional information in brackets
                venue = row.text.split('(')[0].strip()
                break

        # Store all extracted match information in a dictionary
        match_dict = {
            'season': season,
            'league_tier': league_tier,
            'match_date': match_date,
            'match_day': match_day,
            'match_time': match_time,
            'home_club': home_team_name,
            'home_goals': match_home_score,
            'away_club': away_team_name,
            'away_goals': match_away_score,
            'attendance': match_attendance,
            'venue': venue
        }
        match_list.append(match_dict)
        
        # Create checkpoint file after processing every 100 matches
        if (i + 1) % 100 == 0:
            save_progress(match_list, i + 1)
            
    except Exception as e:
        # Log detailed error information including line number for debugging
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        print(f"Error processing URL {url} at line {line_number}: {str(e)}")
        continue

# Save all processed match data to final CSV file
df = pd.DataFrame(match_list)
output_file = output_dir / 'worldfootball_attendance_urls.csv'
df.to_csv(output_file, index=False)
print(f"\nSaved final match data to {output_file}")

# Print summary of successfully processed matches
print(f"\nProcessed {len(match_list)} matches successfully.") 
