"""Module for normalizing attendance4 data from raw files.

This module provides functionality to read and normalize attendance data
from the fourth set of attendance data files, combining them into a standardized format.
The data includes historical match attendance records with dates, teams, scores, and attendance figures.
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


def normalize_date(date_str: str) -> str:
    """Normalize date string to YYYY-MM-DD format.

    Args:
        date_str (str): Date string in format "Day, D. Month YYYY"

    Returns:
        str: Normalized date string in YYYY-MM-DD format

    Raises:
        ValueError: If the date string cannot be parsed
    """
    try:
        if pd.isna(date_str) or not isinstance(date_str, str):
            return None
            
        # Remove any leading/trailing whitespace and quotes
        date_str = date_str.strip().strip('"')
        
        if not date_str:
            return None
            
        # Parse the date using datetime with the correct format
        try:
            date_obj = datetime.strptime(date_str, "%A, %d. %B %Y")
        except ValueError:
            # Try alternative format without day name
            date_str = date_str.split(", ", 1)[1] if ", " in date_str else date_str
            date_obj = datetime.strptime(date_str, "%d. %B %Y")
            
        # Convert to desired format
        return date_obj.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Error parsing date string '{date_str}': {e}")
        return None


def normalize_time(time_str: str) -> str:
    """Normalize time string to 24-hour format (HH:MM).

    Args:
        time_str (str): Time string in any format

    Returns:
        str: Normalized time string in HH:MM format, or empty string if invalid
    """
    try:
        if pd.isna(time_str) or not isinstance(time_str, str):
            return ''
            
        # Remove any leading/trailing whitespace
        time_str = time_str.strip()
        
        if not time_str:
            return ''
            
        # Try parsing the time
        try:
            # For 24-hour format (e.g., "14:30")
            time_obj = datetime.strptime(time_str, "%H:%M")
        except ValueError:
            try:
                # For 12-hour format (e.g., "2:30 PM")
                time_obj = datetime.strptime(time_str, "%I:%M %p")
            except ValueError:
                try:
                    # For 12-hour format without minutes (e.g., "2 PM")
                    time_obj = datetime.strptime(time_str, "%I %p")
                except ValueError:
                    return ''
                    
        # Convert to 24-hour format
        return time_obj.strftime("%H:%M")
    except Exception as e:
        logger.error(f"Error parsing time string '{time_str}': {e}")
        return ''


def clean_numeric(value: str) -> float:
    """Clean numeric values by removing non-numeric characters and converting to float.

    Args:
        value: The value to clean and convert

    Returns:
        float: The cleaned numeric value, or None if invalid
    """
    try:
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        # Remove any non-numeric characters except decimal point
        cleaned = re.sub(r'[^0-9.]', '', str(value))
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def read_attendance4(club_names_normalized: pd.DataFrame) -> None:
    """Read and normalize attendance4 data from raw files.

    This function reads the attendance4 data file, normalizes its contents, and saves
    the result to a CSV file. The function performs several data transformations:
    - Normalizes date format to YYYY-MM-DD as string
    - Normalizes time to 24-hour format (HH:MM)
    - Ensures consistent column naming
    - Normalizes team names using the club name mapping
    - Handles missing values appropriately
    - Cleans numeric values

    Args:
        club_names_normalized (pd.DataFrame): DataFrame containing club name normalization
            mappings with columns 'club_name' and 'club_name_normalized'.

    Raises:
        FileNotFoundError: If the raw attendance data file cannot be found.
        pd.errors.EmptyDataError: If the attendance file is empty.
        ValueError: If the data cannot be properly normalized.
    """
    try:
        # Define paths
        raw_data_path = Path("../../RawData/Matches/Attendance4/attendance4.csv")
        output_path = Path("../../CleansedData/Interim/attendance4.csv")

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Read the attendance data
        logger.info(f"Reading attendance data from {raw_data_path}")
        attendance4 = pd.read_csv(raw_data_path)

        if attendance4.empty:
            raise pd.errors.EmptyDataError("Attendance4 data file is empty")

        try:
            # Normalize date format and ensure it's stored as string
            attendance4['match_date'] = attendance4['match_date'].apply(normalize_date)
            
            # Remove rows with invalid dates
            invalid_dates = attendance4['match_date'].isna()
            if invalid_dates.any():
                logger.warning(f"Removed {invalid_dates.sum()} rows with invalid dates")
                attendance4 = attendance4[~invalid_dates]

            # Normalize time format to 24-hour clock
            attendance4['match_time'] = attendance4['match_time'].apply(normalize_time)

            # Clean numeric columns
            attendance4['attendance'] = attendance4['attendance'].apply(clean_numeric)
            attendance4['match_home_score'] = attendance4['match_home_score'].apply(clean_numeric)
            attendance4['match_away_score'] = attendance4['match_away_score'].apply(clean_numeric)

            # Rename columns to match standard format
            column_mapping = {
                'match_home_score': 'home_goals',
                'match_away_score': 'away_goals',
                'home_team_name': 'home_team',
                'away_team_name': 'away_team'
            }
            attendance4 = attendance4.rename(columns=column_mapping)

            # Normalize team names using the mapping
            for team_col in ['home_team', 'away_team']:
                attendance4 = attendance4.merge(
                    club_names_normalized,
                    left_on=team_col,
                    right_on='club_name',
                    how='left'
                )
                attendance4[team_col] = attendance4['club_name_normalized'].fillna(attendance4[team_col])
                attendance4 = attendance4.drop(['club_name', 'club_name_normalized'], axis=1)

            # Remove rows with missing essential data
            initial_rows = len(attendance4)
            attendance4 = attendance4.dropna(subset=['match_date', 'home_team', 'away_team'])
            dropped_rows = initial_rows - len(attendance4)
            if dropped_rows > 0:
                logger.warning(f"Removed {dropped_rows} rows with missing essential data")

            # Ensure date is stored as string in YYYY-MM-DD format
            attendance4['match_date'] = attendance4['match_date'].astype(str)

            logger.info("Successfully transformed attendance4 data")

        except Exception as e:
            logger.error(f"Error during data transformation: {e}")
            raise ValueError(f"Error during data transformation: {e}")

        # Save the normalized data
        attendance4.to_csv(output_path, index=False)
        logger.success(f"Successfully saved attendance4 data to {output_path}")
        logger.info(f"Total records processed: {len(attendance4)}")

    except Exception as e:
        logger.error(f"Error processing attendance4 data: {e}")
        raise


def main() -> None:
    """Main function to orchestrate the attendance4 data normalization process."""
    try:
        logger.info("Starting attendance4 data normalization process")
        
        # Read club name normalization data
        club_names = read_club_names_normalized()
        logger.info(f"Loaded {len(club_names)} club name mappings")
        
        # Process attendance data
        read_attendance4(club_names)
        
        logger.success("Attendance4 data normalization completed successfully")
    except Exception as e:
        logger.error(f"Error in attendance4 data normalization process: {e}")
        raise


if __name__ == "__main__":
    main() 