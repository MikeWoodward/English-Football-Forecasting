"""Functions for cleansing and normalizing match data from FBRef.

This module provides functionality to normalize team names in match data
by using a reference CSV file containing standardized club names.
"""

import os
from pathlib import Path
import pandas as pd
from typing import Dict, List, Set
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

def correct_matches(FBRef: pd.DataFrame) -> pd.DataFrame:
    """Read and apply match corrections to the FBRef DataFrame.

    This function reads a CSV file containing corrections for matches that were
    incorrectly recorded in the original data. It removes these incorrect matches
    from the provided DataFrame.

    Args:
        FBRef (pd.DataFrame): DataFrame containing the match data to be corrected.

    Returns:
        pd.DataFrame: Corrected version of the input DataFrame with false matches removed.

    Raises:
        FileNotFoundError: If the corrections file is not found.
        pd.errors.EmptyDataError: If the corrections file is empty.
    """
    try:
        # Read the corrections file
        corrections_path = Path('../../CleansedData/Corrections and normalization/FBRef-corrections.csv')
        false_matches = pd.read_csv(corrections_path)
        logger.info(f"Successfully loaded corrections data with {len(false_matches)} entries")

        # Store initial number of rows
        initial_rows = len(FBRef)

        # Create a merge key from all common columns between FBRef and false_matches
        common_columns = list(set(FBRef.columns) & set(false_matches.columns))
        
        if not common_columns:
            logger.warning("No common columns found between FBRef and corrections file")
            return FBRef

        # Identify rows to remove using an anti-merge
        FBRef_corrected = FBRef.merge(
            false_matches[common_columns],
            how='left',
            indicator=True
        )
        
        # Keep only rows that don't match with false_matches
        FBRef_corrected = FBRef_corrected[FBRef_corrected['_merge'] == 'left_only']
        FBRef_corrected = FBRef_corrected.drop(columns=['_merge'])

        # Calculate and log the number of rows removed
        rows_removed = initial_rows - len(FBRef_corrected)
        logger.info(f"Removed {rows_removed} false matches from the DataFrame")
        
        if rows_removed == 0:
            logger.warning("No matches were found to remove - check if the corrections file contains the correct data")

        return FBRef_corrected

    except FileNotFoundError:
        logger.error(f"Corrections file not found at {corrections_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error("Corrections file is empty")
        raise
    except Exception as e:
        logger.error(f"Error in correct_matches: {str(e)}")
        raise

def normalize_FBRef(club_names: pd.DataFrame) -> None:
    """Normalize team names in FBRef match data and save the results.

    Reads all CSV files from the FBRef matches folder, combines them into a single
    DataFrame, and normalizes both home and away team names using the provided
    club names mapping. Also extracts league tier and season from filenames.

    Args:
        club_names: DataFrame containing club name normalization mappings

    Raises:
        FileNotFoundError: If the FBRef data directory or output directory doesn't exist
        ValueError: If no CSV files are found in the FBRef directory or if filenames don't match expected format
    """
    try:
        # Get list of all CSV files in the FBRef matches directory
        fbref_path = Path('../../RawData/Matches/FBRef')
        csv_files = list(fbref_path.glob('*.csv'))
        
        if not csv_files:
            logger.error(f"No CSV files found in {fbref_path}")
            raise ValueError("No CSV files found in FBRef directory")

        # Read and combine all CSV files into a single DataFrame
        dfs = []
        for file in csv_files:
            try:
                # Extract league tier and season from filename
                filename = file.stem  # Get filename without extension
                
                # Extract league tier (first character before underscore)
                league_tier_match = re.match(r'^(\d)_', filename)
                if not league_tier_match:
                    logger.error(f"Invalid filename format for league tier in {file.name}")
                    raise ValueError(f"Filename must start with a number followed by underscore: {file.name}")
                league_tier = int(league_tier_match.group(1))
                
                # Extract season (last 9 characters)
                if len(filename) < 9:
                    logger.error(f"Filename too short to extract season in {file.name}")
                    raise ValueError(f"Filename too short to contain season: {file.name}")
                season = filename[-9:]
                
                # Read the CSV file
                df = pd.read_csv(file)
                
                # Add league_tier and season columns
                df['league_tier'] = league_tier
                df['season'] = season
                
                dfs.append(df)
                logger.info(f"Successfully loaded {file.name} with league tier {league_tier} and season {season}")
            except Exception as e:
                logger.error(f"Error reading {file.name}: {str(e)}")
                continue

        # Concatenate all DataFrames into one
        FBRef = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined {len(dfs)} CSV files into one DataFrame")

        # Remove columns that are not needed for analysis
        columns_to_drop = ['source', 'referee', 'match_report', 'notes']
        FBRef = FBRef.drop(columns=columns_to_drop, errors='ignore')
        logger.info("Dropped unnecessary columns")

        # Standardize column names to lowercase and rename columns
        column_renames = {
            'date': 'match_date',
            'start_time': 'match_time',
            'dayofweek': 'day_of_week'
        }
        FBRef = FBRef.rename(columns=column_renames)
        logger.info("Renamed date and time columns")

        # Convert abbreviated day names to full day names
        day_mapping = {
            'Mon': 'Monday',
            'Tue': 'Tuesday',
            'Wed': 'Wednesday',
            'Thu': 'Thursday',
            'Fri': 'Friday',
            'Sat': 'Saturday',
            'Sun': 'Sunday'
        }
        if 'day_of_week' in FBRef.columns:
            FBRef['day_of_week'] = FBRef['day_of_week'].map(day_mapping)
            logger.info("Converted day names to full format")
        else:
            logger.warning("day_of_week column not found in the DataFrame")

        # Check for unmapped team names before normalization
        known_clubs: Set[str] = set(club_names['club_name'].unique())
        
        # Find unmapped home teams
        unmapped_home_teams = set(FBRef['home_team'].unique()) - known_clubs
        if unmapped_home_teams:
            logger.error(f"Found {len(unmapped_home_teams)} unmapped home teams:")
            for team in sorted(unmapped_home_teams):
                logger.error(f"  - {team}")
                
        # Find unmapped away teams
        unmapped_away_teams = set(FBRef['away_team'].unique()) - known_clubs
        if unmapped_away_teams:
            logger.error(f"Found {len(unmapped_away_teams)} unmapped away teams:")
            for team in sorted(unmapped_away_teams):
                logger.error(f"  - {team}")
                
        # Report total number of unmapped teams
        all_unmapped = unmapped_home_teams | unmapped_away_teams
        if all_unmapped:
            logger.error(f"Total unique unmapped teams: {len(all_unmapped)}")
            raise ValueError("Found unmapped teams in the dataset. Please update the club name normalization mapping.")
        else:
            logger.info("All teams have corresponding entries in the normalization mapping")

        # Normalize home team names by merging with the club names mapping
        FBRef = FBRef.merge(
            club_names,
            left_on='home_team',
            right_on='club_name',
            how='left'
        )
        # Rename normalized column and remove the temporary join column
        FBRef = FBRef.rename(columns={'club_name_normalized': 'home_club'}).drop(columns=['club_name'], errors='ignore')
        
        # Normalize away team names by merging with the club names mapping
        FBRef = FBRef.merge(
            club_names,
            left_on='away_team',
            right_on='club_name',
            how='left',
            suffixes=('', '_away')
        )
        # Rename normalized column and remove the temporary join column
        FBRef = FBRef.rename(columns={'club_name_normalized': 'away_club'}).drop(columns=['club_name'], errors='ignore')

        # Remove original team name columns as we now have normalized versions
        FBRef = FBRef.drop(columns=['away_team', 'home_team'], errors='ignore')  

        # Sort the DataFrame by multiple columns
        FBRef = FBRef.sort_values(
            by=['season', 'match_date', 'league_tier', 'home_club'],
            ascending=[True, True, True, True]
        )
        logger.info("Sorted DataFrame by season, match_date, league_tier, and home_club")

        # Apply corrections to the DataFrame
        FBRef = correct_matches(FBRef)
        logger.info("Applied corrections to the DataFrame")

        # Ensure output directory exists
        output_dir = Path('../../CleansedData/Interim')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save the processed data to CSV
        output_path = output_dir / 'FBRef.csv'
        FBRef.to_csv(output_path, index=False)
        logger.info(f"Normalized data saved to {output_path}")

    except Exception as e:
        logger.error(f"Error in normalize_FBRef: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting club name normalization process")
        # Read the club names mapping
        club_names_df = read_club_names()
        
        # Normalize the FBRef data using the mapping
        normalize_FBRef(club_names_df)
        
        logger.info("Club name normalization process completed successfully")
    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        raise 