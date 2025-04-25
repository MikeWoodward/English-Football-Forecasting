"""Module for normalizing attendance data from raw files.

This module provides functionality to read and normalize club names and attendance data
from various source files, combining them into a standardized format.
"""

import os
from pathlib import Path
from typing import List
from datetime import datetime
import re

import pandas as pd
from loguru import logger


def read_club_names_normalized() -> pd.DataFrame:
    """Read and load the club name normalization mapping.

    This function reads the club name normalization file that contains mappings between
    various versions of club names and their standardized forms.

    Returns:
        pd.DataFrame: A DataFrame containing the club name normalization mappings with
            columns 'club_name' and 'club_name_normalized'.

    Raises:
        FileNotFoundError: If the club name normalization file cannot be found.
        pd.errors.EmptyDataError: If the file is empty.
    """
    try:
        file_path = Path("../../CleansedData/Corrections and normalization/club_name_normalization.csv")
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


def clean_attendance(value: str) -> int:
    """Clean attendance value by removing non-numeric characters and decimal points.
    
    Args:
        value (str): The attendance value to clean.
        
    Returns:
        int: The cleaned attendance value as an integer.
    """
    try:
        # Remove any non-numeric characters except decimal points
        cleaned = re.sub(r'[^\d.]', '', str(value))
        # Remove decimal point and any following digits
        cleaned = cleaned.replace('.', '')  
        return int(cleaned) if cleaned else 0
    except Exception as e:
        logger.warning(f"Error cleaning attendance value '{value}': {e}")
        return 0


def read_attendance1(club_names_normalized: pd.DataFrame) -> None:
    """Read and normalize attendance data from raw files.

    This function reads all attendance data files from the raw data directory,
    combines them into a single DataFrame, and saves the normalized result to a CSV file.
    The function handles data from multiple seasons and quarters, combining them while
    maintaining data integrity.

    The function performs the following transformations:
    - Renames 'date' column to 'match_date' and standardizes format to YYYY-MM-DD
    - Renames 'time' column to 'match_time' and standardizes to 24-hour format
    - Renames 'tier' column to 'league_tier'
    - Cleans attendance column by removing non-numeric characters
    - Left joins with club_names_normalized for both home and away teams to get standardized names
    - Drops original team name columns in favor of normalized versions
    
    Args:
        club_names_normalized (pd.DataFrame): DataFrame containing club name normalization
            mappings with columns 'club_name' and 'club_name_normalized'.

    Raises:
        FileNotFoundError: If the raw attendance data directory cannot be found.
        pd.errors.EmptyDataError: If any of the attendance files are empty.
        ValueError: If no valid attendance data could be read from any file.
    """
    try:
        # Define paths
        raw_data_path = Path("../../RawData/Matches/Attendance")
        output_path = Path("../../CleansedData/Interim/attendance1.csv")

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get list of all attendance CSV files
        attendance_files = sorted([f for f in raw_data_path.glob("attendance_*.csv")])
        
        if not attendance_files:
            logger.error("No attendance files found in the raw data directory")
            raise FileNotFoundError("No attendance files found in the raw data directory")

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
        attendance1 = pd.concat(attendance_dfs, ignore_index=True)
        
        # Perform column transformations
        try:
            # Convert and standardize date format
            attendance1['date'] = pd.to_datetime(attendance1['date']).dt.strftime('%Y-%m-%d')
            
            # Convert and standardize time format (assuming time is in a recognizable format)
            attendance1['time'] = pd.to_datetime(attendance1['time'], format='mixed').dt.strftime('%H:%M')
            
            # Replace any times that are 00:00 with a null value
            attendance1['time'] = attendance1['time'].replace('00:00', pd.NA)
            
            # Clean attendance column
            attendance1['attendance'] = attendance1['attendance'].apply(clean_attendance)
            logger.info("Successfully cleaned attendance values")
            
            # Rename columns
            attendance1 = attendance1.rename(columns={
                'date': 'match_date',
                'time': 'match_time',
                'tier': 'league_tier',
                'home team': 'home_team',
                'away team': 'away_team'  # Ensure consistent column naming
            })
            
            # Left join with club_names_normalized for home teams
            attendance1 = attendance1.merge(
                club_names_normalized,
                left_on='home_team',
                right_on='club_name',
                how='left'
            )
            # Rename the normalized column and drop the temporary join column
            attendance1 = attendance1.rename(columns={'club_name_normalized': 'home_club'})
            attendance1 = attendance1.drop(columns=['club_name'])
            logger.info("Successfully joined with club names normalization data for home teams")
            
            # Left join with club_names_normalized for away teams
            attendance1 = attendance1.merge(
                club_names_normalized,
                left_on='away_team',
                right_on='club_name',
                how='left'
            )
            # Rename the normalized column and drop the temporary join column
            attendance1 = attendance1.rename(columns={'club_name_normalized': 'away_club'})
            attendance1 = attendance1.drop(columns=['club_name'])
            logger.info("Successfully joined with club names normalization data for away teams")
            
            # Drop unnecessary columns
            columns_to_drop = ['league', 'source_file', 'home_team', 'away_team']
            attendance1 = attendance1.drop(columns=columns_to_drop, errors='ignore')
            
            logger.info("Successfully transformed column names and formats")
            
        except Exception as e:
            logger.error(f"Error during column transformations: {e}")
            raise ValueError(f"Error during column transformations: {e}")

        # Save the combined and transformed data
        attendance1 = clean_data(attendance1)
        attendance1.to_csv(output_path, index=False)
        logger.success(f"Successfully saved normalized attendance data to {output_path}")
        logger.info(f"Total records processed: {len(attendance1)}")

    except Exception as e:
        logger.error(f"Error processing attendance data: {e}")
        raise


def clean_data(attendance1: pd.DataFrame) -> pd.DataFrame:
    """Clean specific data entries in the attendance DataFrame.

    This function applies specific data cleaning rules to fix known issues
    in the attendance data.

    Args:
        attendance1 (pd.DataFrame): The attendance DataFrame to clean.

    Returns:
        pd.DataFrame: The cleaned attendance DataFrame.
    """
    # Find the specific Crystal Palace vs Coventry City match from 2006-2007
    # and update its date and time if they are missing
    mask = (
        (attendance1['home_club'] == 'Crystal Palace') &
        (attendance1['away_club'] == 'Coventry City') &
        (attendance1['season'] == '2006-2007') &
        (attendance1['match_date'].isna()) &
        (attendance1['match_time'].isna())
    )
    
    if mask.any():
        attendance1.loc[mask, 'match_date'] = '2006-09-23'
        attendance1.loc[mask, 'match_time'] = '10:00'
        logger.info("Updated missing date and time for Crystal Palace vs Coventry City match")
    
    return attendance1


def main() -> None:
    """Main function to orchestrate the attendance data normalization process.
    
    This function coordinates the reading of club name normalization data and
    the processing of attendance data files.
    """
    try:
        logger.info("Starting attendance data normalization process")
        
        # Read club name normalization data
        club_names = read_club_names_normalized()
        logger.info(f"Loaded {len(club_names)} club name mappings")
        
        # Process attendance data
        read_attendance1(club_names)
        
        logger.success("Attendance data normalization completed successfully")
    except Exception as e:
        logger.error(f"Error in attendance data normalization process: {e}")
        raise


if __name__ == "__main__":
    main() 