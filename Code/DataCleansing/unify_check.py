"""Data unification and validation module.

This module provides functionality to unify and validate data from various 
sources, ensuring consistency and data quality across the dataset.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

def read_fbref_data() -> pd.DataFrame:
    """Read and validate the FBRef dataset.

    This function reads the FBRef.csv file from the CleansedData/Interim 
    folder and performs initial validation checks.

    Returns:
        pd.DataFrame: The loaded FBRef dataset.

    Raises:
        DataValidationError: If the file cannot be read or validation fails.
        FileNotFoundError: If the FBRef.csv file is not found.

    Example:
        >>> fbref_df = read_fbref_data()
        >>> print(fbref_df.shape)
    """
    try:
        file_path = Path('../../CleansedData/Interim/FBRef.csv')
        logger.info(f"Reading FBRef data from {file_path.absolute()}")
        
        if not file_path.exists():
            msg = f"FBRef data file not found at {file_path.absolute()}"
            raise FileNotFoundError(msg)
        
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded FBRef data with shape {df.shape}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error reading FBRef data: {str(e)}")
        raise DataValidationError(f"Failed to read FBRef data: {str(e)}")

def read_football_data() -> pd.DataFrame:
    """Read and validate the Football-data dataset.

    This function reads the Football-data.csv file from the 
    CleansedData/Interim folder and performs initial validation checks.

    Returns:
        pd.DataFrame: The loaded Football-data dataset.

    Raises:
        DataValidationError: If the file cannot be read or validation fails.
        FileNotFoundError: If the Football-data.csv file is not found.

    Example:
        >>> football_df = read_football_data()
        >>> print(football_df.shape)
    """
    try:
        file_path = Path('../../CleansedData/Interim/Football-data.csv')
        logger.info(f"Reading Football-data from {file_path.absolute()}")
        
        if not file_path.exists():
            msg = f"Football-data file not found at {file_path.absolute()}"
            raise FileNotFoundError(msg)
        
        df = pd.read_csv(file_path)
        msg = f"Successfully loaded Football-data with shape {df.shape}"
        logger.info(msg)
        
        return df
    
    except Exception as e:
        logger.error(f"Error reading Football-data: {str(e)}")
        raise DataValidationError(f"Failed to read Football-data: {str(e)}")

def read_attendance1_data() -> pd.DataFrame:
    """Read and validate the attendance1 dataset.

    This function reads the attendance1.csv file from the 
    CleansedData/Interim folder and performs initial validation checks.

    Returns:
        pd.DataFrame: The loaded attendance1 dataset.

    Raises:
        DataValidationError: If the file cannot be read or validation fails.
        FileNotFoundError: If the attendance1.csv file is not found.

    Example:
        >>> attendance_df = read_attendance1_data()
        >>> print(attendance_df.shape)
    """
    try:
        file_path = Path('../../CleansedData/Interim/attendance1.csv')
        logger.info(f"Reading attendance1 data from {file_path.absolute()}")
        
        if not file_path.exists():
            msg = f"attendance1 data file not found at {file_path.absolute()}"
            raise FileNotFoundError(msg)
        
        df = pd.read_csv(file_path)
        msg = f"Successfully loaded attendance1 data with shape {df.shape}"
        logger.info(msg)
        
        return df
    
    except Exception as e:
        logger.error(f"Error reading attendance1 data: {str(e)}")
        msg = f"Failed to read attendance1 data: {str(e)}"
        raise DataValidationError(msg)

def read_attendance2_data() -> pd.DataFrame:
    """Read and validate the attendance2 dataset.

    This function reads the attendance2.csv file from the 
    CleansedData/Interim folder and performs initial validation checks.

    Returns:
        pd.DataFrame: The loaded attendance2 dataset.

    Raises:
        DataValidationError: If the file cannot be read or validation fails.
        FileNotFoundError: If the attendance2.csv file is not found.

    Example:
        >>> attendance2_df = read_attendance2_data()
        >>> print(attendance2_df.shape)
    """
    try:
        file_path = Path('../../CleansedData/Interim/attendance2.csv')
        logger.info(f"Reading attendance2 data from {file_path.absolute()}")
        
        if not file_path.exists():
            msg = f"attendance2 data file not found at {file_path.absolute()}"
            raise FileNotFoundError(msg)
        
        df = pd.read_csv(file_path)
        msg = f"Successfully loaded attendance2 data with shape {df.shape}"
        logger.info(msg)
        
        return df
    
    except Exception as e:
        logger.error(f"Error reading attendance2 data: {str(e)}")
        msg = f"Failed to read attendance2 data: {str(e)}"
        raise DataValidationError(msg)

def remove_null_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Remove matches involving Bury FC in the 2019-2020 season.

    Args:
        df (pd.DataFrame): The merged dataset containing match information.

    Returns:
        pd.DataFrame: Dataset with specified matches removed.

    Example:
        >>> cleaned_df = remove_null_matches(merged_df)
    """
    mask = ~(
        (df['season'] == '2019-2020') & 
        ((df['home_club'] == 'Bury FC') | (df['away_club'] == 'Bury FC'))
    )
    return df[mask].copy()

def verify_merged(df: pd.DataFrame) -> bool:
    """Verify the integrity of the merged dataset.

    This function performs several validation checks on the merged dataset:
    1. Checks for null or empty match dates
    2. Identifies clubs playing multiple matches on the same day
    3. Detects clubs appearing in multiple league tiers in the same season

    Args:
        df (pd.DataFrame): The merged dataset to verify

    Returns:
        bool: True if all checks pass, False if any validation errors found

    Raises:
        DataValidationError: If critical validation errors are found
    """
    validation_passed = True
    
    # Check 1: Null or empty match dates
    null_dates = df[df['match_date'].isna()]
    if not null_dates.empty:
        validation_passed = False
        logger.error(f"Found {len(null_dates)} rows with null match dates:")
        for _, row in null_dates.iterrows():
            msg = (
                f"  {row['home_club']} vs {row['away_club']} - "
                f"Season: {row['season']}"
            )
            logger.error(msg)
    
    # Check 2: Clubs playing multiple matches on same day
    for date in df['match_date'].unique():
        matches_on_date = df[df['match_date'] == date]
        clubs = pd.concat([
            matches_on_date['home_club'], 
            matches_on_date['away_club']
        ]).unique()
        
        for club in clubs:
            club_matches = matches_on_date[
                (matches_on_date['home_club'] == club) | 
                (matches_on_date['away_club'] == club)
            ]
            if len(club_matches) > 1:
                validation_passed = False
                logger.error(f"Club {club} has multiple matches on {date}:")
                for _, match in club_matches.iterrows():
                    msg = f"  {match['home_club']} vs {match['away_club']}"
                    logger.error(msg)
    
    # Check 3: Clubs in multiple tiers in same season
    for season in df['season'].unique():
        season_data = df[df['season'] == season]
        all_clubs = pd.concat([
            season_data['home_club'], 
            season_data['away_club']
        ]).unique()
        
        for club in all_clubs:
            club_tiers = season_data[
                (season_data['home_club'] == club) | 
                (season_data['away_club'] == club)
            ]['league_tier'].unique()
            
            if len(club_tiers) > 1:
                validation_passed = False
                msg = (
                    f"Club {club} appears in multiple tiers "
                    f"({', '.join(map(str, club_tiers))}) in season {season}"
                )
                logger.error(msg)
    
    if validation_passed:
        logger.info("All data validation checks passed successfully")
    else:
        msg = "Data validation checks found issues in the merged dataset"
        logger.warning(msg)
    
    return validation_passed

def main() -> Dict[str, Any]:
    """Main function to unify and check data from multiple sources.

    This function loads both FBRef and Football-data datasets, performs data 
    validation, and generates comprehensive reports about the data quality.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - fbref_data: The loaded and validated FBRef dataset
            - football_data: The loaded and validated Football-data dataset
            - merged: The merged dataset from both sources
            - validation_reports: Individual reports for each dataset
            - errors: List of any errors encountered during processing

    Raises:
        DataValidationError: If there are critical issues during processing.
    """
    logger.info("Starting data unification and validation process...")
    try:
        # Initialize results dictionary
        results = {
            'fbref_data': None,
            'football_data': None,
            'merged': None,
            'validation_reports': {},
            'errors': []
        }
        
        # Load FBRef data
        try:
            results['fbref_data'] = read_fbref_data()
            logger.info("Successfully loaded FBRef data")
        except Exception as e:
            logger.error(f"Error loading FBRef data: {str(e)}")
            results['errors'].append({
                'source': 'FBRef',
                'error': str(e)
            })

        # Load Football-data
        try:
            results['football_data'] = read_football_data()
            logger.info("Successfully loaded Football-data")
        except Exception as e:
            logger.error(f"Error loading Football-data: {str(e)}")
            results['errors'].append({
                'source': 'Football-data',
                'error': str(e)
            })

        # Check if we have both datasets loaded
        if results['fbref_data'] is None or results['football_data'] is None:
            raise DataValidationError("Failed to load one or both datasets")

        # Merge datasets
        try:
            logger.info("Merging datasets...")
            merge_columns = [
                'home_goals', 'away_goals', 'league_tier', 'season',
                'match_date', 'home_club', 'away_club'
            ]
            
            results['merged'] = pd.merge(
                results['fbref_data'],
                results['football_data'],
                how='outer',
                on=merge_columns,
                suffixes=('_fbref', '_football')
            )
            
            # Create match_time_merged column
            logger.info("Creating match_time_merged column...")
            results['merged']['match_time_merged'] = results['merged'].apply(
                lambda row: (
                    row['match_time_fbref'] 
                    if (pd.notna(row['match_time_fbref']) and 
                        pd.isna(row['match_time_football']))
                    else row['match_time_football'] 
                    if (pd.isna(row['match_time_fbref']) and 
                        pd.notna(row['match_time_football']))
                    else row['match_time_fbref'] 
                    if row['match_time_fbref'] == row['match_time_football']
                    else None
                ),
                axis=1
            )
            
            # Drop original match_time columns and rename match_time_merged
            msg = "Dropping original match_time columns and renaming..."
            logger.info(msg)
            
            # Drop original columns
            results['merged'] = results['merged'].drop(
                columns=['match_time_fbref', 'match_time_football']
            )
            
            # Rename merged column
            results['merged'] = results['merged'].rename(
                columns={'match_time_merged': 'match_time'}
            )
            
            # Load attendance1 data and merge with existing dataset
            attendance1_df = read_attendance1_data()
            
            # Merge with attendance1 data
            results['merged'] = pd.merge(
                results['merged'],
                attendance1_df,
                # Use outer join to keep all matches from both datasets
                how='outer',
                # Match on these key columns
                on=['match_date', 'home_club', 'away_club', 'league_tier', 
                    'season'],
                suffixes=('_merge1', '_attendance1')
            )   
            
            # Load attendance2 data and merge with existing dataset
            attendance2_df = read_attendance2_data()
            
            # Merge with attendance2 data
            results['merged'] = pd.merge(
                results['merged'],
                attendance2_df,
                # Use outer join to keep all matches from both datasets
                how='outer',
                # Match on these key columns
                on=['match_date', 'home_club', 'away_club', 'season', 
                    'home_goals', 'away_goals', 'league_tier'],
                suffixes=('', '_attendance2')
            ) 
            # Drop duplicates
            results['merged'] = results['merged'].drop_duplicates()
            
            # Sort the merged dataset
            results['merged'] = results['merged'].sort_values(
                by=['match_date', 'season', 'league_tier', 'home_club', 
                    'away_club']
            )
            
            # Log merge completion
            shape_str = str(results['merged'].shape)
            msg = f"Successfully merged datasets. Shape: {shape_str}"
            logger.info(msg)
            
            # Verify the merged dataset
            logger.info("Verifying merged dataset...")
            verify_merged(results['merged'])
            
            # Save merged dataset
            output_path = Path('../../CleansedData/Interim/temp.csv')
            results['merged'].to_csv(output_path, index=False)
            logger.info(f"Saved merged dataset to {output_path.absolute()}")
            
        except Exception as e:
            logger.error(f"Error merging datasets: {str(e)}")
            results['errors'].append({
                'source': 'merge',
                'error': str(e)
            })

        logger.info("Data loading and merging completed")
        return results

    except Exception as e:
        logger.error(f"Error in main processing: {str(e)}")
        raise DataValidationError(f"Main processing failed: {str(e)}")

if __name__ == "__main__":
    try:
        result = main()
        logger.info("Processing completed successfully")
        
        # Print summary of loaded and merged data
        if result['fbref_data'] is not None:
            print(f"FBRef data shape: {result['fbref_data'].shape}")
        if result['football_data'] is not None:
            print(f"Football-data shape: {result['football_data'].shape}")
        if result['merged'] is not None:
            print(f"Merged data shape: {result['merged'].shape}")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")