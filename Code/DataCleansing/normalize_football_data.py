"""Functions for cleansing and normalizing match data from Football-data.

This module provides functionality to normalize team names in match data
by using a reference CSV file containing standardized club names.
"""

import os
from pathlib import Path
import pandas as pd
from typing import Dict, List
import logging
import re
from datetime import datetime

# Configure logging with timestamp, logger name, level and message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_club_names() -> pd.DataFrame:
    """Read and load the club name normalization data.

    Reads the club_name_normalization.csv file which contains mappings
    between various versions of club names and their standardized forms.

    Returns:
        pd.DataFrame: DataFrame containing club name mappings with columns:
            - club_name: Original club name
            - club_name_normalized: Standardized club name

    Raises:
        FileNotFoundError: If the club_name_normalization.csv file is not found
        pd.errors.EmptyDataError: If the CSV file is empty
    """
    try:
        # Read the mapping file containing standardized club names
        file_path = Path('../../CleansedData/Corrections and normalization/club_name_normalization.csv')
        club_names = pd.read_csv(file_path)
        logger.info(f"Successfully loaded club names data with {len(club_names)} entries")
        return club_names
    except FileNotFoundError:
        logger.error(f"Club names file not found at {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error("Club names file is empty")
        raise

def normalize_football_data(club_names: pd.DataFrame) -> None:
    """Normalize team names in Football-data match data and save the results.

    Reads all CSV files from the Football-data matches folder, combines them into a single
    DataFrame, and normalizes both home and away team names using the provided
    club names mapping.

    Args:
        club_names: DataFrame containing club name normalization mappings

    Raises:
        FileNotFoundError: If the Football-data directory or output directory doesn't exist
        ValueError: If no CSV files are found in the Football-data directory
    """
    try:
        # Get list of all CSV files in the Football-data matches directory
        football_data_path = Path('../../RawData/Matches/Football-data')
        csv_files = list(football_data_path.glob('*.csv'))
        
        if not csv_files:
            logger.error(f"No CSV files found in {football_data_path}")
            raise ValueError("No CSV files found in Football-data directory")

        # Read and combine all CSV files into a single DataFrame
        dfs = []
        for file in csv_files:
            try:
                # Extract league tier and season from filename
                filename = file.name
                # Validate and extract league tier (should be 1-5 followed by underscore)
                if not re.match(r'^[1-5]_', filename):
                    logger.error(f"Invalid filename format for league tier in {filename}")
                    continue
                
                league_tier = int(filename[0])
                season = filename[-13:-4]  # Extract YYYY-YYYY format without underscore
                
                # Read the CSV and add the extracted information
                df = pd.read_csv(file)
                df['league_tier'] = league_tier
                df['season'] = season
                
                dfs.append(df)
                logger.info(f"Successfully loaded {file.name} (Tier: {league_tier}, Season: {season})")
            except Exception as e:
                logger.error(f"Error reading {file.name}: {str(e)}")
                continue

        # Concatenate all DataFrames into one
        Football_data = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined {len(dfs)} CSV files into one DataFrame")

        # Keep only the required columns, including the new ones
        columns_to_keep = ['match_date', 'match_time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'league_tier', 'season']
        Football_data = Football_data[columns_to_keep]
        logger.info("Kept only required columns")

        # Check for unmapped team names
        home_teams = set(Football_data['HomeTeam'].unique())
        away_teams = set(Football_data['AwayTeam'].unique())
        known_teams = set(club_names['club_name'])

        unmapped_home_teams = home_teams - known_teams
        unmapped_away_teams = away_teams - known_teams

        if unmapped_home_teams:
            logger.error(f"Found {len(unmapped_home_teams)} unmapped home teams: {sorted(unmapped_home_teams)}")
        if unmapped_away_teams:
            logger.error(f"Found {len(unmapped_away_teams)} unmapped away teams: {sorted(unmapped_away_teams)}")

        # Normalize home team names by merging with the club names mapping
        Football_data = Football_data.merge(
            club_names,
            left_on='HomeTeam',
            right_on='club_name',
            how='left'
        )
        # Rename normalized column and remove the temporary join column
        Football_data = Football_data.rename(columns={'club_name_normalized': 'home_club'}).drop(columns=['club_name'])
        
        # Normalize away team names by merging with the club names mapping
        Football_data = Football_data.merge(
            club_names,
            left_on='AwayTeam',
            right_on='club_name',
            how='left'
        )
        # Rename normalized column and remove the temporary join column
        Football_data = Football_data.rename(columns={
            'club_name_normalized': 'away_club',
            'FTAG': 'away_goals',
            'FTHG': 'home_goals'
        }).drop(columns=['club_name'])

        # Drop the original team name columns as we now have normalized versions
        Football_data = Football_data.drop(columns=['HomeTeam', 'AwayTeam'])
        logger.info("Dropped original team name columns")

        # Sort the DataFrame
        Football_data = Football_data.sort_values(
            by=['season', 'match_date', 'league_tier', 'home_club'],
            ascending=[True, True, True, True]
        )
        logger.info("Sorted DataFrame by season, match_date, league_tier, and home_club")

        # Ensure output directory exists
        output_dir = Path('../../CleansedData/Interim')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save the processed data to CSV
        output_path = output_dir / 'Football-data.csv'
        Football_data.to_csv(output_path, index=False)
        logger.info(f"Normalized data saved to {output_path}")

    except Exception as e:
        logger.error(f"Error in normalize_football_data: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting club name normalization process for Football-data")
        # Read the club names mapping
        club_names_df = read_club_names()
        
        # Normalize the Football-data data using the mapping
        normalize_football_data(club_names_df)
        
        logger.info("Club name normalization process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        raise 