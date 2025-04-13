# Import required libraries
# requests: for making HTTP requests to fetch web pages
# BeautifulSoup: for parsing HTML content
# os and Path: for handling file paths cross-platform
# traceback and sys: for detailed error reporting
# pandas: for data manipulation and CSV handling
# time: for adding delays between requests
import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path
import traceback
import sys
import pandas as pd
import time

# Define the path to the input file containing match URLs
# Using Path for cross-platform compatibility
match_urls_path = Path('../../RawData/Matches/MatchURLs/match_urls.txt')

# Try to read the URLs from the file
# If file doesn't exist, create empty list and show error
try:
    with open(match_urls_path, 'r', encoding='utf-8') as file:
        match_list_urls = file.read().splitlines()
except FileNotFoundError:
    print(f"Error: Could not find file at {match_urls_path}")
    match_list_urls = []

# Initialize empty list to store match data dictionaries
match_list = []

# Create the output directory if it doesn't exist
output_dir = Path('../../CleansedData/Normalization')
output_dir.mkdir(parents=True, exist_ok=True)

# Function to save current progress to CSV
def save_progress(data, step_number):
    """
    Save the current match data to a CSV file
    Args:
        data: List of match dictionaries
        step_number: Current step number for filename
    """
    # Convert match_list to pandas DataFrame
    df = pd.DataFrame(data)
    # Create filename with step number
    output_file = output_dir / f'attendance2_checkpoint_{step_number}.csv'
    # Save to CSV without index
    df.to_csv(output_file, index=False)
    print(f"\nCheckpoint saved: {output_file}")

# Process each URL in the list
for i, url in enumerate(match_list_urls):
    try:
        # Add a polite delay between requests (2 seconds)
        if i > 0:  # Don't delay on the first request
            time.sleep(2)
            
        # Make HTTP request to get the webpage content
        print(f"Processing URL {i+1} of {len(match_list_urls)}: {url}")
        response = requests.get(url)
        match_page = response.text
        
        # Create BeautifulSoup object to parse HTML
        soup = BeautifulSoup(match_page, 'html.parser')
        
        # Find all tables with class 'standard_tabelle'
        # These tables contain the match information
        tables = soup.find_all('table', class_='standard_tabelle')
        
        # Skip if no tables found
        if not tables:
            print(f"Warning: No tables found with class 'standard_tabelle' for URL: {url}")
            continue
        
        # Get the first table which contains main match details
        first_table = tables[0]
        rows = first_table.find_all('tr')
        
        # Skip if table has no rows
        if not rows:
            print(f"Warning: No rows found in the table for URL: {url}")
            continue
            
        # Process the first row which contains team names and match timing
        first_row = rows[0]
        columns = first_row.find_all('th')
        
        # Ensure we have enough columns for home team, date/time, and away team
        if len(columns) < 3:
            print(f"Warning: Not enough columns in first row for URL: {url}")
            continue
        
        # Extract home team name from first column's anchor tag
        home_team_link = columns[0].find('a')
        if not home_team_link:
            print(f"Warning: No home team link found for URL: {url}")
            continue
        home_team_name = home_team_link.text.strip()
        
        # Extract date and time from second column
        # Some entries have date and time separated by <br> tag
        if (br_tag := columns[1].find('br')):
            # If <br> exists, get text before and after it
            match_date = br_tag.previous_sibling.strip() if br_tag.previous_sibling else ''
            match_time = br_tag.next_sibling.strip() if br_tag.next_sibling else ''
            # Remove 'Clock' text if present in time
            if 'Clock' in match_time:
                match_time = match_time.replace('Clock', '').strip()
        else:
            # If no <br>, entire text is the date
            match_date = columns[1].text.strip()
            match_time = ''
        
        # Extract away team name from third column's anchor tag
        away_team_link = columns[2].find('a')
        if not away_team_link:
            print(f"Warning: No away team link found for URL: {url}")
            continue
        away_team_name = away_team_link.text.strip()
        
        # Extract match score from second row
        if len(rows) < 2:
            print(f"Warning: No second row found for URL: {url}")
            continue
            
        # Get cells from second row and ensure enough columns exist
        second_row_cells = rows[1].find_all('td')
        if len(second_row_cells) < 2:
            print(f"Warning: Not enough columns in second row for URL: {url}")
            continue
        match_score = second_row_cells[1].text.strip().split(":")
        match_home_score = match_score[0]
        match_away_score = match_score[1]
        
        # Extract attendance
        rows = tables[-1].find_all('tr')
        for row in rows:
            image = row.find('img')
            if image and image['title'] == 'Attendance':
                match_attendance = row.text.strip().replace(".", "")
                break
        else:
            match_attendance = None
        
        # Create dictionary with all match information
        match_dict = {
            'match_date': match_date,
            'match_time': match_time,
            'home_team_name': home_team_name,
            'away_team_name': away_team_name,
            'match_home_score': match_home_score,
            'match_away_score': match_away_score,
            'attendance': match_attendance
        }
        # Add match dictionary to the list of matches
        match_list.append(match_dict)
        
        # Save progress every 100 matches
        if (i + 1) % 100 == 0:
            save_progress(match_list, i + 1)
            
    except Exception as e:
        # If any error occurs, get the line number and error details
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        print(f"Error processing URL {url} at line {line_number}: {str(e)}")
        continue

# Save final results to CSV
# Convert match_list to pandas DataFrame
df = pd.DataFrame(match_list)

# Save to final CSV file
output_file = output_dir / 'attendance2.csv'
df.to_csv(output_file, index=False)
print(f"\nSaved final match data to {output_file}")

# Print summary of processed matches
print(f"\nProcessed {len(match_list)} matches successfully.") 
