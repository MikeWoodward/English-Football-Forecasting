"""Module for cleansing attendance2 data from EPL matches.

This module provides functions to read, validate, and normalize attendance2 data
from multiple CSV files.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
import logging
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_attandance2() -> pd.DataFrame:
    """Read and concatenate all attendance2 CSV files into a single DataFrame.
    
    Returns:
        pd.DataFrame: Concatenated DataFrame containing all attendance2 data.
        
    Raises:
        FileNotFoundError: If the attendance2 directory does not exist.
        ValueError: If no CSV files are found in the directory.
    """
    data_dir = Path("../../RawData/Matches/Attendance2")
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Directory not found: {data_dir}")
    
    # Find all CSV files in the directory
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {data_dir}")
    
    # Read and concatenate all CSV files
    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            logger.info(f"Successfully read {file.name}")
        except Exception as e:
            logger.error(f"Error reading {file.name}: {str(e)}")
            continue
    
    if not dfs:
        raise ValueError("No valid CSV files could be read")
    
    attendance2 = pd.concat(dfs, ignore_index=True)
    logger.info(f"Successfully concatenated {len(dfs)} files into a single DataFrame")
    
    return attendance2

def check_data(attendance2: pd.DataFrame) -> Tuple[bool, str]:
    """Check the attendance2 DataFrame for data quality issues.
    
    Args:
        attendance2 (pd.DataFrame): DataFrame containing attendance2 data.
        
    Returns:
        Tuple[bool, str]: A tuple containing:
            - bool: True if all checks pass, False otherwise
            - str: Summary of issues found
            
    Raises:
        ValueError: If required columns are missing from the DataFrame.
    """
    required_columns = ['home_club', 'away_club', 'home_goals', 'away_goals', 'match_date']
    missing_columns = [col for col in required_columns if col not in attendance2.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    issues = []
    
    # Check for missing values
    for col in required_columns:
        missing_count = attendance2[col].isna().sum()
        if missing_count > 0:
            issues.append(f"Column '{col}' has {missing_count} missing values")
    
    # Check for non-numeric values in numeric columns
    goals_columns = ['home_goals', 'away_goals']
    for col in goals_columns:
        if col in attendance2.columns:
            # For goals columns, don't accept null values
            non_numeric = pd.to_numeric(attendance2[col], errors='coerce').isna().sum()
            if non_numeric > 0:
                issues.append(f"Column '{col}' has {non_numeric} non-numeric or null values")
    
    # Check attendance column separately, allowing null values
    if 'attendance' in attendance2.columns:
        # Convert to numeric, keeping null values
        attendance_numeric = pd.to_numeric(attendance2['attendance'], errors='coerce')
        # Count only non-numeric values that aren't null
        non_numeric_attendance = ((~attendance2['attendance'].isna()) & 
                                (attendance_numeric.isna())).sum()
        if non_numeric_attendance > 0:
            issues.append(f"Column 'attendance' has {non_numeric_attendance} non-numeric values (excluding nulls)")
    
    # Log issues
    if issues:
        for issue in issues:
            logger.warning(issue)
        return False, "\n".join(issues)
    
    logger.info("All data quality checks passed")
    return True, "No issues found"

def normalize_club_names(attendance2: pd.DataFrame) -> pd.DataFrame:
    """Normalize club names in the attendance2 DataFrame using a normalization mapping.
    
    Args:
        attendance2 (pd.DataFrame): DataFrame containing attendance2 data.
        
    Returns:
        pd.DataFrame: DataFrame with normalized club names.
        
    Raises:
        FileNotFoundError: If the club name normalization file is not found.
    """
    try:
        # Read the club name normalization file
        norm_file = Path("../../CleansedData/Corrections and normalization/club_name_normalization.csv")
        if not norm_file.exists():
            logger.warning(f"Club name normalization file not found at {norm_file}. Skipping normalization.")
            return attendance2
            
        normalized_club_names = pd.read_csv(norm_file)
        logger.info("Successfully loaded club name normalization data")
        
        # Normalize home club names
        attendance2 = attendance2.merge(
            normalized_club_names,
            left_on='home_club',
            right_on='club_name',
            how='left'
        )
        attendance2['home_club'] = attendance2['club_name_normalized'].fillna(attendance2['home_club'])
        attendance2 = attendance2.drop(columns=['club_name', 'club_name_normalized'])
        
        # Normalize away club names
        attendance2 = attendance2.merge(
            normalized_club_names,
            left_on='away_club',
            right_on='club_name',
            how='left'
        )
        attendance2['away_club'] = attendance2['club_name_normalized'].fillna(attendance2['away_club'])
        attendance2 = attendance2.drop(columns=['club_name', 'club_name_normalized'])
        
        logger.info("Successfully normalized club names")
        return attendance2
        
    except Exception as e:
        logger.error(f"Error during club name normalization: {str(e)}")
        return attendance2

def cleanse_data(attendance2: pd.DataFrame) -> pd.DataFrame:
    """Clean the attendance2 DataFrame by handling missing values and data inconsistencies.
    
    Args:
        attendance2 (pd.DataFrame): DataFrame containing attendance2 data.
        
    Returns:
        pd.DataFrame: Cleaned DataFrame with standardized missing values.
    """
    # Replace string "nan" with actual null values in attendance column
    if 'attendance' in attendance2.columns:
        attendance2['attendance'] = attendance2['attendance'].replace('nan', np.nan)
        logger.info("Replaced string 'nan' with null values in attendance column")
    
    return attendance2

if __name__ == "__main__":
    try:
        # Read the data
        attendance2_df = read_attandance2()
        
        # Cleanse the data
        attendance2_df = cleanse_data(attendance2_df)
        
        # Check data quality
        is_valid, issues = check_data(attendance2_df)
        if not is_valid:
            logger.warning("Data quality issues found:\n" + issues)
        
        # Normalize club names
        attendance2_df = normalize_club_names(attendance2_df)
        
        # Save the cleansed data
        output_dir = Path("../../CleansedData/Interim")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "attendance2.csv"
        attendance2_df.to_csv(output_file, index=False)
        logger.info(f"Successfully saved cleansed data to {output_file}")
        
    except Exception as e:
        logger.error(f"Error processing attendance2 data: {str(e)}")
        raise 