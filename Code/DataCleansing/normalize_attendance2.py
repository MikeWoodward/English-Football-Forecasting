"""Module for normalizing attendance2 data from raw files.

This module provides functionality to read and normalize attendance data
from the second set of attendance data files, combining them into a standardized
format.
"""

import os
from pathlib import Path
from typing import List, Set
from datetime import datetime
import re

import pandas as pd
from loguru import logger


def read_club_names_normalized() -> pd.DataFrame:
    """Read and load the club name normalization mapping.

    This function reads the club name normalization file that contains mappings
    between various versions of club names and their standardized forms.

    Returns:
        pd.DataFrame: A DataFrame containing the club name normalization mappings
            with columns 'club_name' and 'club_name_normalized'.

    Raises:
        FileNotFoundError: If the club name normalization file cannot be found.
        pd.errors.EmptyDataError: If the file is empty.
    """
    try:
        file_path = Path(
            "../../CleansedData/Corrections and normalization/"
            "club_name_normalization.csv"
        )
        club_names_normalized = pd.read_csv(file_path)
        logger.info(f"Successfully loaded club name normalization data from {file_path}")
        return club_names_normalized
    except FileNotFoundError as e:
        logger.error(f"Club name normalization file not found at {file_path}")
        raise FileNotFoundError(f"Club name normalization file not found: {e}")
    except pd.errors.EmptyDataError as e:
        logger.error(f"Club name normalization file is empty: {file_path}")
        raise pd.errors.EmptyDataError(f"Club name normalization file is empty: {e}")
    except Exception as e:
        logger.error(f"Error reading club name normalization file: {e}")
        raise


def validate_club_names(
    attendance_df: pd.DataFrame, 
    club_names_normalized: pd.DataFrame
) -> None:
    """Validate that all club names in attendance data exist in normalization mapping.

    Args:
        attendance_df (pd.DataFrame): DataFrame containing attendance data with
            'Home Team' and 'Away Team' columns
        club_names_normalized (pd.DataFrame): DataFrame containing club name
            normalization mappings

    Raises:
        ValueError: If any club names are found that don't exist in the
            normalization mapping
    """
    # Get unique club names from both home and away teams
    home_teams = set(attendance_df['Home Team'].unique())
    away_teams = set(attendance_df['Away Team'].unique())
    all_teams = home_teams.union(away_teams)
    
    # Get the set of valid club names from normalization mapping
    valid_club_names = set(club_names_normalized['club_name'].unique())
    
    # Find any club names that don't exist in the mapping
    missing_clubs = all_teams - valid_club_names
    
    if missing_clubs:
        error_msg = (
            "Found club names in attendance data that don't exist in normalization "
            "mapping:\n"
        )
        for club in sorted(missing_clubs):
            error_msg += f"- {club}\n"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("All club names in attendance data have corresponding mappings")


def read_attendance2(club_names_normalized: pd.DataFrame) -> None:
    """Read and normalize attendance2 data from raw files.

    This function reads all attendance data files from the Attendance2 raw data
    directory, combines them into a single DataFrame, and saves the normalized
    result to a CSV file.
    The function performs several data transformations:
    - Validates all club names exist in normalization mapping
    - Creates a 'season' column from source_file names
    - Removes 'Round' and 'Competition' columns
    - Renames score columns to 'home_goals' and 'away_goals'
    - Renames 'Attendance' to 'attendance'
    - Splits 'Date/Time' into 'match_date' and 'match_time'
    - Drops unnecessary columns

    Args:
        club_names_normalized (pd.DataFrame): DataFrame containing club name
            normalization mappings with columns 'club_name' and
            'club_name_normalized'.

    Raises:
        FileNotFoundError: If the raw attendance data directory cannot be found.
        pd.errors.EmptyDataError: If any of the attendance files are empty.
        ValueError: If no valid attendance data could be read from any file or if
            club names are missing from normalization mapping.
    """
    try:
        # Define paths
        raw_data_path = Path("../../RawData/Matches/Attendance2")
        output_path = Path("../../CleansedData/Interim/attendance2.csv")

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get list of all CSV files in the directory
        attendance_files = sorted([f for f in raw_data_path.glob("*.csv")])
        
        if not attendance_files:
            logger.error("No attendance files found in the raw data directory")
            raise FileNotFoundError(
                "No attendance files found in the raw data directory"
            )

        # Read and combine all attendance files
        attendance_dfs: List[pd.DataFrame] = []
        for file in attendance_files:
            try:
                df = pd.read_csv(file)
                # Add source file information for tracking
                df['source_file'] = file.name
                attendance_dfs.append(df)
                logger.debug(f"Successfully read attendance file: {file.name}")
            except pd.errors.EmptyDataError as e:
                logger.warning(f"Empty attendance file encountered: {file.name}")
                continue
            except Exception as e:
                logger.warning(f"Error reading file {file.name}: {e}")
                continue

        if not attendance_dfs:
            logger.error("No valid attendance data could be read from any file")
            raise ValueError("No valid attendance data could be read from any file")

        # Combine all DataFrames
        attendance2 = pd.concat(attendance_dfs, ignore_index=True)
        
        # Validate club names before proceeding with normalization
        validate_club_names(attendance2, club_names_normalized)
        
        try:
            # Create season column from source_file
            attendance2['season'] = attendance2['source_file'].str.replace(
                '.csv', ''
            )
            
            # Split Date/Time into match_date and match_time
            attendance2[['match_date', 'match_time']] = (
                attendance2['Date/Time'].str.split(' ', n=1, expand=True)
            )
            # Convert date to standard format, explicitly handling UK date format
            attendance2['match_date'] = pd.to_datetime(
                attendance2['match_date'], 
                format='%d/%m/%Y'
            ).dt.strftime('%Y-%m-%d')
            # Ensure match_time is in 24-hour format and handle missing values
            attendance2['match_time'] = attendance2['match_time'].fillna('')
            
            # Rename columns
            attendance2 = attendance2.rename(columns={
                'Home Score': 'home_goals',
                'Away Score': 'away_goals',
                'Attendance': 'attendance'
            })
            
            # Left join with club_names_normalized for home teams
            attendance2 = attendance2.merge(
                club_names_normalized,
                left_on='Home Team',
                right_on='club_name',
                how='left'
            )
            # Rename the normalized column and drop the temporary join column
            attendance2 = attendance2.rename(
                columns={'club_name_normalized': 'home_club'}
            )
            attendance2 = attendance2.drop(columns=['Home Team', 'club_name'])
            logger.info(
                "Successfully joined with club names normalization data for home teams"
            )
            
            # Left join with club_names_normalized for away teams
            attendance2 = attendance2.merge(
                club_names_normalized,
                left_on='Away Team',
                right_on='club_name',
                how='left'
            )
            # Rename the normalized column and drop the temporary join column
            attendance2 = attendance2.rename(
                columns={'club_name_normalized': 'away_club'}
            )
            attendance2 = attendance2.drop(columns=['Away Team', 'club_name'])
            logger.info(
                "Successfully joined with club names normalization data for away teams"
            )

            # Drop unnecessary columns
            columns_to_drop = ['Round', 'Competition', 'source_file', 'Date/Time']
            attendance2 = attendance2.drop(columns=columns_to_drop, errors='ignore')

            # drop any duplicates
            attendance2 = attendance2.drop_duplicates()
            
            logger.info("Successfully transformed attendance2 data")
            
        except Exception as e:
            logger.error(f"Error during data transformation: {e}")
            raise ValueError(f"Error during data transformation: {e}")
        
        # Save the combined and transformed data
        attendance2.to_csv(output_path, index=False)
        logger.success(f"Successfully saved attendance2 data to {output_path}")
        logger.info(f"Total records processed: {len(attendance2)}")

    except Exception as e:
        logger.error(f"Error processing attendance2 data: {e}")
        raise


def main() -> None:
    """Main function to orchestrate the attendance2 data normalization process."""
    try:
        logger.info("Starting attendance2 data normalization process")
        
        # Read club name normalization data
        club_names = read_club_names_normalized()
        logger.info(f"Loaded {len(club_names)} club name mappings")
        
        # Process attendance data
        read_attendance2(club_names)
        
        logger.success("Attendance2 data normalization completed successfully")
    except Exception as e:
        logger.error(f"Error in attendance2 data normalization process: {e}")
        raise


if __name__ == "__main__":
    main() 