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

# Standard library imports
import os
import sys
import time
import traceback
from pathlib import Path

# Third-party imports
import pandas as pd
import requests
from bs4 import BeautifulSoup

# File paths configuration
# Using Path for cross-platform compatibility and better path handling
match_urls_path = Path('../../RawData/Matches/MatchURLs/match_urls.txt')

# Try to read the URLs from the file
# If file doesn't exist, create empty list and show error
try:
    with open(match_urls_path, 'r', encoding='utf-8') as file:
        match_list_urls = file.read().splitlines()
except FileNotFoundError:
    print(f"Error: Could not find file at {match_urls_path}")
    match_list_urls = []

# Initialize data structures
match_list = []  # List to store match data dictionaries

# Create output directory structure
output_dir = Path('../../RawData/Matches/Attendance4')
output_dir.mkdir(parents=True, exist_ok=True)

def save_progress(data: list, step_number: int) -> None:
    """Save the current match data to a CSV checkpoint file.

    Creates a checkpoint CSV file containing all processed match data up to the current point.
    Useful for data recovery in case of script interruption.

    Args:
        data: List of dictionaries containing match information.
        step_number: Current processing step number used in the checkpoint filename.

    Returns:
        None. Saves data to a CSV file and prints confirmation message.
    """
    df = pd.DataFrame(data)
    output_file = output_dir / f'attendance2_checkpoint_{step_number}.csv'
    df.to_csv(output_file, index=False)
    print(f"\nCheckpoint saved: {output_file}")

# Main processing loop - iterate through each match URL
for i, url in enumerate(match_list_urls):
    try:
        # Add a polite delay between requests to avoid overwhelming the server
        if i > 0:  # Skip delay for first request
            time.sleep(2)
            
        # Fetch and parse the webpage content
        print(f"Processing URL {i+1} of {len(match_list_urls)}: {url}")
        response = requests.get(url)
        match_page = response.text
        soup = BeautifulSoup(match_page, 'html.parser')
        
        # Find match information tables
        # The page structure has multiple 'standard_tabelle' tables
        tables = soup.find_all('table', class_='standard_tabelle')
        
        if not tables:
            print(f"Warning: No tables found with class 'standard_tabelle' for URL: {url}")
            continue
        
        # Process main match details from the first table
        first_table = tables[0]
        rows = first_table.find_all('tr')
        
        if not rows:
            print(f"Warning: No rows found in the table for URL: {url}")
            continue
            
        # Extract team names and match timing from the first row
        first_row = rows[0]
        columns = first_row.find_all('th')
        
        # Validate column count
        if len(columns) < 3:
            print(f"Warning: Not enough columns in first row for URL: {url}")
            continue
        
        # Extract home team information
        home_team_link = columns[0].find('a')
        if not home_team_link:
            print(f"Warning: No home team link found for URL: {url}")
            continue
        home_team_name = home_team_link.text.strip()
        
        # Extract match date and time
        # Handle cases where date and time are separated by <br> tag
        if (br_tag := columns[1].find('br')):
            match_date = br_tag.previous_sibling.strip() if br_tag.previous_sibling else ''
            match_time = br_tag.next_sibling.strip() if br_tag.next_sibling else ''
            match_time = match_time.replace('Clock', '').strip()  # Clean up time format
        else:
            match_date = columns[1].text.strip()
            match_time = ''
        
        # Extract away team information
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
        
        # Parse the score (format: "home_score:away_score")
        match_score = second_row_cells[1].text.strip().split(":")
        match_home_score = match_score[0]
        match_away_score = match_score[1]
        
        # Extract attendance from the last table
        # Look for row with attendance icon
        rows = tables[-1].find_all('tr')
        match_attendance = None
        for row in rows:
            image = row.find('img')
            if image and image['title'] == 'Attendance':
                match_attendance = row.text.strip().replace(".", "")  # Remove thousand separators
                break
        
        # Create structured match data dictionary
        match_dict = {
            'match_date': match_date,
            'match_time': match_time,
            'home_team_name': home_team_name,
            'away_team_name': away_team_name,
            'match_home_score': match_home_score,
            'match_away_score': match_away_score,
            'attendance': match_attendance
        }
        match_list.append(match_dict)
        
        # Create periodic checkpoints
        if (i + 1) % 100 == 0:
            save_progress(match_list, i + 1)
            
    except Exception as e:
        # Detailed error logging with line numbers
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        print(f"Error processing URL {url} at line {line_number}: {str(e)}")
        continue

# Save final results
df = pd.DataFrame(match_list)
output_file = output_dir / 'attendance4.csv'
df.to_csv(output_file, index=False)
print(f"\nSaved final match data to {output_file}")

# Print processing summary
print(f"\nProcessed {len(match_list)} matches successfully.") 
