"""
match_attendance2.py - Football Attendance Data Downloader

This script downloads football attendance data from footballwebpages.co.uk by:
1. Constructing URLs for each season's data
2. Downloading CSV files
3. Saving files to the specified folder with formatted filenames (YYYY-YYYY.csv)
4. Reading the data into pandas DataFrames and filtering for relevant competitions

Author: Mike Woodward
Date: April 2024
"""

import os
import time
import sys
from pathlib import Path
from typing import Tuple, Optional
import numpy as np

# Check for required packages
try:
    import requests
    import pandas as pd
except ImportError:
    print("Error: The 'requests' and 'pandas' packages are required. Please install it using:")
    print("pip install requests pandas")
    sys.exit(1)

# Define competitions to exclude, organized by category
EXCLUDED_COMPETITIONS = [
    # English Domestic Cups (Including historical sponsored names)
    'FA Cup', 'Emirates FA Cup', 'FA Cup with Budweiser', 'FA Cup sponsored by E.ON',
    'Carabao Cup', 'Carling Cup', 'Capital One Cup', 'EFL Cup',
    'Community Shield', "Papa John's Trophy", "Johnstone's Paint Trophy",
    'Checkatrade Trophy', 'Buildbase FA Trophy', 'FA Trophy',
    'Isuzu FA Trophy', 'LDV Vans Trophy', 'Alan Turvey Trophy',
    'BigFreeBet.com Challenge Cup', 'Robert Dyas League Cup',
    'Leasing.com Trophy',
    
    # European Competitions
    'UEFA Champions League', 'UEFA Europa League', 'Europa League',
    'UEFA Europa Conference League', 'UEFA Super Cup',
    
    # International Competitions
    'World Cup', 'World Cup Qualification', 'European Championship',
    'European Championship Qualification', 'Africa Cup of Nations',
    'Copa América', 'Club World Cup', 'International Friendly',
    'UEFA Nations League', 'Internationals',
    
    # Scottish Football (Including historical sponsored names)
    # -- Premier League/Premiership
    'Scottish Premiership', 'Cinch Premiership', 'Ladbrokes Premiership',
    'Clydesdale Bank Scottish Premier League',
    # -- Lower Divisions
    'Scottish Championship', 'Cinch Championship', 'Ladbrokes Championship',
    'Scottish League One', 'Cinch League One', 'Ladbrokes League One',
    'Scottish League Two', 'Cinch League Two', 'Ladbrokes League Two',
    'Irn Bru Scottish League Division One',
    'Irn Bru Scottish League Division Two',
    'Irn Bru Scottish League Division Three',
    # -- Cups
    'William Hill Scottish Cup', 'Scottish FA Cup', 'Betfred Cup',
    "Tunnock's Challenge Cup", 'IRN-BRU Cup', 'Scottish Communities Cup',
    'Petrofac Training Cup', 'Ramsdens Cup',
    
    # Other Top European Leagues
    'German Bundesliga', 'Italian Serie A', 'Spanish La Liga',
    'French Ligue 1', 'Belgian First Division A', 'Dutch Eredivisie',
    'Portuguese Primeira Liga', 'Turkish Süper Lig', 'Russian Premier League',
    
    # English Non-League Football
    # -- National League (Including historical names)
    'Vanarama National League North', 'Vanarama National League South',
    'National League North', 'National League South',
    'Vanarama Conference North', 'Vanarama Conference South',
    'Skrill Premier', 'Skrill North', 'Skrill South',
    'Blue Square Bet Premier', 'Blue Square Bet North', 'Blue Square Bet South',
    
    # -- Northern Premier League (Including historical names)
    'Northern Premier League - Premier Division',
    'Northern Premier League - East Division',
    'Northern Premier League - West Division',
    'Northern Premier League - Midlands Division',
    'Northern Premier League - South East Division',
    'Northern Premier League - North West Division',
    'BetVictor Northern Premier Division',
    'BetVictor Northern South East Division',
    'BetVictor Northern North West Division',
    'Evo-Stik League Premier Division',
    'Evo-Stik League First Division East',
    'Evo-Stik League First Division West',
    'Evo-Stik League Division One North',
    'Evo-Stik League Division One South',
    'Evo-Stik League First Division North',
    'Evo-Stik League First Division South',
    'Evo-Stik North League Premier Division',
    'Evo-Stik North League Division One North',
    'Evo-Stik North League Division One South',
    'Evo-Stik League Cup',
    
    # -- Isthmian League (Including historical names)
    'Isthmian League - Premier Division',
    'Isthmian League - North Division',
    'Isthmian League - South Central Division',
    'Isthmian League - South East Division',
    'BetVictor Isthmian Premier Division',
    'BetVictor Isthmian North Division',
    'BetVictor Isthmian South Central Division',
    'BetVictor Isthmian South East Division',
    'Bostik League Premier Division',
    'Bostik League North Division',
    'Bostik League South Division',
    'Bostik League South Central Division',
    'Bostik League South East Division',
    'Ryman League Premier Division',
    'Ryman League Division One North',
    'Ryman League Division One South',
    
    # -- Southern League (Including historical names)
    'Southern League - Premier Central',
    'Southern League - Premier South',
    'Southern League - Central Division',
    'Southern League - South Division',
    'BetVictor Southern Premier Central',
    'BetVictor Southern Premier South',
    'BetVictor Southern Central Division',
    'BetVictor Southern South Division',
    'Evo-Stik Southern Premier Central',
    'Evo-Stik Southern Premier South',
    'Evo-Stik Southern Division One Central',
    'Evo-Stik Southern Division One South',
    'Evo-Stik Southern League Premier Division',
    'Evo-Stik Southern League Division One Central',
    'Evo-Stik Southern League Division One South & West',
    'Evo-Stik South League Premier Division',
    'Evo-Stik South League Division One Central',
    'Evo-Stik South League Division One South & West',
    'Evo-Stik South Premier',
    'Evo-Stik South East',
    'Evo-Stik South West',
    'Calor League Premier Division',
    'Calor League Division One Central',
    'Calor League Division One South & West',
    
    # Women's Football
    "Women's World Cup", "Women's European Championship",
    "Women's International Friendly",
    "FA Women's Super League", "FA Women's Championship",
    "FA Women's League Cup", "Vitality Women's FA Cup",
    "SSE Women's FA Cup",
    "FA Women's National League South",
    "FA Women's National League North",
    "FA Women's National League East",
    "FA Women's National League West",
    "FA Women's National League Midlands",
    "FA Women's National League North East",
    "FA Women's National League North West",
    "FA Women's National League South East",
    "FA Women's National League South West",
    "FA Women's National League West Midlands",
    "FA Women's National League Yorkshire & Humberside",
    "FA Women's National League Scotland",
    "FA Women's National League Wales",
    
    # Regional Competitions
    'Northern Ireland Premiership', 'Welsh Premier League',
    'Pitching In Super Cup', 'Velocity Cup', 'Velocity Trophy',
    'CSS League Challenge Cup', 'Integro League Cup',
    'Welsh Premier League',
    
    # County Cups and Regional Trophies
    'Berks and Bucks County Cup', 'Birmingham Senior Cup',
    'Cambridgeshire Invitation Cup', 'Cambridge County Cup',
    'Cheshire Senior Cup', 'Cumberland Senior Cup',
    'Derbyshire Senior Cup', 'Durham Senior Cup',
    'East Riding County Cup', 'Essex Senior Cup',
    'Essex County Cup', 'Hampshire Cup',
    'Hertfordshire County Cup', 'Huntingdonshire Senior Cup',
    'Kent Senior Cup', 'Lancashire FA Challenge Trophy',
    'Leicestershire Challenge Cup', 'Lincolnshire Senior Cup',
    'Liverpool County FA Senior Cup', 'London County Cup',
    'Manchester Premier Cup', 'Middlesex County Cup',
    'Norfolk County Cup', 'Norfolk Senior Cup',
    'North Riding Senior Cup', 'Northamptonshire Senior Cup',
    'Northumberland Senior Cup', 'Nottinghamshire Senior Cup',
    'Sheffield & Hallam Senior Cup', 'Staffordshire Senior Cup',
    'Suffolk County Cup', 'Surrey Senior Cup', 'Sussex County Cup',
    'The West Riding County Cup', 'Walsall Senior Cup',
    'Shropshire Senior Cup',
    
    # Mid Cheshire District FA Cups
    'Mid Cheshire District FA Senior Cup',
    'Mid Cheshire District FA Challenge Cup',
    'Mid Cheshire District FA Charity Cup',
    "Mid Cheshire District FA President's Cup",
    "Mid Cheshire District FA Chairman's Cup",
    "Mid Cheshire District FA Vice-Chairman's Cup",
    "Mid Cheshire District FA Secretary's Cup",

    "Papa John's Trophy",
    "Papa John’s Trophy",
    
    # Other
    'Friendly'
]

def create_output_directory() -> str:
    """
    Create the output directory if it doesn't exist.
    
    Returns:
        str: Path to the output directory
    """
    # Get the user's home directory
    home_dir = str(Path.home())
    
    # Construct the full path
    project_root = os.path.join(home_dir, 'Documents', 'Projects', 'Python', 'EPL predictor')
    output_dir = os.path.join(project_root, 'RawData', 'Matches', 'Attendance2')
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Files will be saved to: {output_dir}")
    return output_dir

def download_file(url: str, output_path: str) -> Tuple[bool, Optional[pd.DataFrame]]:
    """
    Download a file from a URL, save it to the specified path, and read it into a pandas DataFrame.
    Filters out non-Premier League competitions.
    
    Args:
        url (str): URL to download from
        output_path (str): Path to save the file to
        
    Returns:
        Tuple[bool, Optional[pd.DataFrame]]: A tuple containing:
            - bool: True if successful, False otherwise
            - Optional[pd.DataFrame]: The loaded and filtered DataFrame if successful, None otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Save the response content to file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Read the CSV file into a pandas DataFrame
        attendance2 = pd.read_csv(output_path)
        
        # Filter out excluded competitions
        if 'Competition' in attendance2.columns:
            initial_rows = len(attendance2)
            attendance2 = attendance2[~attendance2['Competition'].isin(EXCLUDED_COMPETITIONS)]
            print(attendance2['Competition'].unique())
            filtered_rows = len(attendance2)
            print(f"Filtered out {initial_rows - filtered_rows} non-top-tier matches")

        # Filter out rounds
        if 'Round' in attendance2.columns:
            attendance2 = attendance2[attendance2['Round'].isna()]

        # add a league_tier column
        if 'Competition' in attendance2.columns:
            conditions = [
                (attendance2['Competition'].str.contains('Premiership|Premier League', case=False, na=False)),
                (attendance2['Competition'].str.contains('Championship', case=False, na=False)),
                (attendance2['Competition'].str.contains('League One', case=False, na=False)),
                (attendance2['Competition'].str.contains('League Two', case=False, na=False)),
                (attendance2['Competition'].str.contains('National League|Conference', case=False, na=False))
            ]
            values = [1, 2, 3, 4, 5]
            attendance2['league_tier'] = pd.NA
            attendance2['league_tier'] = np.select(conditions, values, default=pd.NA)

        # Drop unnecessary columns that we don't need for analysis
        # Using errors='ignore' to handle cases where columns might not exist
        attendance2 = attendance2.drop(
            ['Competition', 'Round'], 
            axis=1, 
            errors='ignore'
        )
        
        # Define mapping of original column names to new standardized names
        # Following Python naming conventions (lowercase with underscores)
        column_renames = {
            # Raw attendance number
            'Attendance': 'attendance',
            # Name of home team
            'Home Team': 'home_club',
            # Name of away team
            'Away Team': 'away_club',
            # Goals scored by home team
            'Home Score': 'home_goals',
            # Goals scored by away team
            'Away Score': 'away_goals'
        }
        
        # Apply the column renaming to the DataFrame
        attendance2 = attendance2.rename(columns=column_renames)

        # Split Date/Time column and format dates
        if 'Date/Time' in attendance2.columns:
            # Initialize match_time column with NaN values
            attendance2['match_time'] = pd.NA
            attendance2['match_date'] = pd.NA
            
            # Handle rows with Date/Time values
            mask = attendance2['Date/Time'].notna()
            if mask.any():
                # Split into temporary columns
                split_dt = attendance2.loc[mask, 'Date/Time'].str.split(' ', expand=True)
                
                # Assign date values where we have them
                attendance2.loc[mask, 'match_date'] = pd.to_datetime(
                    split_dt[0], 
                    format='%d/%m/%Y'
                ).dt.strftime('%Y-%m-%d')
                
                # Assign time values only where they exist (column 1 from split)
                if split_dt.shape[1] > 1:
                    time_mask = mask & split_dt[1].notna()
                    if time_mask.any():
                        attendance2.loc[time_mask, 'match_time'] = split_dt[1].loc[time_mask].str.zfill(5)
            
            # Drop the original Date/Time column
            attendance2 = attendance2.drop('Date/Time', axis=1)

        # Clean up attendance
        if 'attendance' in attendance2.columns:
            # Convert attendance column to strings first
            attendance2['attendance'] = attendance2['attendance'].astype(str)
            # Handle nulls safely using fillna() - temporarily fill nulls with empty string
            attendance2['attendance'] = attendance2['attendance'].fillna('')
            attendance2['attendance'] = attendance2['attendance'].str.replace('sold out', '')
            # Restore nulls where we had empty strings
            attendance2.loc[attendance2['attendance'] == '', 'attendance'] = pd.NA

        # Save the processed data
        attendance2.to_csv(output_path, index=False)
        
        return True, attendance2
    
    except Exception as e:
        print(f"Error downloading/processing {url}: {e}")
        return False, None

def download_attendance_data() -> dict[str, pd.DataFrame]:
    """
    Download attendance data from footballwebpages.co.uk and load into DataFrames.
    
    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping season names to their corresponding attendance DataFrames
    """
    base_url = "https://www.footballwebpages.co.uk/archive.csv?season={filename}"
    filenames = [
        "20222023.csv", "20212022.csv", "20202021.csv", "20192020.csv",
        "20182019.csv", "20172018.csv", "20162017.csv", "20152016.csv",
        "20142015.csv", "20132014.csv", "20122013.csv", 
        "20112012.csv",
        "20102011.csv", "20092010.csv", "20082009.csv", "20072008.csv",
        "20062007.csv", "20052006.csv", "20042005.csv"
    ]
    
    output_dir = create_output_directory()
    print(f"\nFound {len(filenames)} seasons to download")
    
    # Dictionary to store DataFrames for each season
    attendance_data = {}
    
    # Download each file
    successful_downloads = 0
    for i, filename in enumerate(filenames, 1):
        # Construct URL using original filename format
        url = base_url.format(filename=filename.replace('.csv', ''))
        
        # Transform filename to include hyphen (e.g., 2022-2023.csv)
        formatted_filename = f"{filename[:4]}-{filename[4:8]}.csv"
        output_path = os.path.join(output_dir, formatted_filename)
        
        print(f"\nDownloading file {i} of {len(filenames)}: {formatted_filename}")
        print(f"URL: {url}")
        
        success, df = download_file(url, output_path)
        if success:
            print(f"Successfully downloaded and processed {formatted_filename}")
            season_key = formatted_filename.replace('.csv', '')
            attendance_data[season_key] = df
            successful_downloads += 1
        else:
            print(f"Failed to download/process {formatted_filename}")
        
        # Add a small delay between downloads to be polite
        time.sleep(1)
    
    print(f"\nDownload process completed! Successfully downloaded and processed {successful_downloads} of {len(filenames)} files")
    
    # Print summary of loaded data
    print("\nData Summary:")
    for season, df in attendance_data.items():
        print(f"{season}: {len(df)} matches")
    
    return attendance_data

def main() -> dict[str, pd.DataFrame]:
    """
    Main function to orchestrate the download process and data loading.
    
    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping season names to their corresponding attendance DataFrames
    """
    try:
        print("Starting attendance data download...")
        attendance_data = download_attendance_data()
        print("\nProcess completed successfully!")
        return attendance_data
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 