"""Script to read, combine, and clean attendance1 data.

This script provides functions to:
1. Read and concatenate multiple attendance1 data files
2. Normalize club names for consistency
3. Perform data quality checks
4. Save the cleaned data to disk
"""

import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def read_concat_attendance1() -> pd.DataFrame:
    """Read and concatenate all attendance1 data files.
    
    Returns:
        DataFrame containing concatenated attendance1 data
        
    Raises:
        FileNotFoundError: If no attendance1 files are found in the directory
    """
    # Get the current script's directory
    current_dir = Path(__file__).parent
    
    # Construct the path to the attendance1 data directory
    attendance_dir = current_dir / ".." / ".." / "RawData" / "Matches" / "Attendance1"
    attendance_dir = attendance_dir.resolve()
    
    # Check if directory exists
    if not attendance_dir.exists():
        raise FileNotFoundError(f"Directory not found: {attendance_dir}")
    
    # Find all CSV files in the directory
    csv_files = list(attendance_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {attendance_dir}")
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    # Read and concatenate all CSV files
    dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            logger.info(f"Successfully read {file.name}")
        except Exception as e:
            logger.error(f"Error reading {file.name}: {str(e)}")
            raise
    
    # Concatenate all dataframes
    attendance1 = pd.concat(dfs, ignore_index=True)
    logger.info(f"Successfully concatenated {len(dfs)} files into one DataFrame")
    
    return attendance1

def normalize_club_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize club names in the attendance1 data.
    
    Args:
        df: DataFrame containing attendance1 data with club names
        
    Returns:
        DataFrame with normalized club names
        
    Raises:
        FileNotFoundError: If the club name normalization file is not found
        KeyError: If required columns are missing from either DataFrame
    """
    # Get the current script's directory
    current_dir = Path(__file__).parent
    
    # Construct the path to the normalization file
    norm_file_path = current_dir / ".." / ".." / "CleansedData" / "Corrections and normalization" / "club_name_normalization.csv"
    norm_file_path = norm_file_path.resolve()
    
    # Check if file exists
    if not norm_file_path.exists():
        raise FileNotFoundError(f"Club name normalization file not found: {norm_file_path}")
    
    # Read the normalization mapping
    normalize_club_name = pd.read_csv(norm_file_path)
    logger.info("Successfully loaded club name normalization mapping")
    
    # Check for unmatched home clubs
    unmatched_home = df[~df["home_club"].isin(normalize_club_name["club_name"])]["home_club"].unique()
    if len(unmatched_home) > 0:
        logger.warning(f"Found {len(unmatched_home)} unmatched home clubs:")
        for club in sorted(unmatched_home):
            logger.warning(f"  - {club}")
    
    # Check for unmatched away clubs
    unmatched_away = df[~df["away_club"].isin(normalize_club_name["club_name"])]["away_club"].unique()
    if len(unmatched_away) > 0:
        logger.warning(f"Found {len(unmatched_away)} unmatched away clubs:")
        for club in sorted(unmatched_away):
            logger.warning(f"  - {club}")
    
    # Normalize home club names
    df = df.merge(
        normalize_club_name,
        left_on="home_club",
        right_on="club_name",
        how="left"
    )
    df = df.drop(columns=["home_club", "club_name"])
    df = df.rename(columns={"club_name_normalized": "home_club"})
    logger.info("Normalized home club names")
    
    # Normalize away club names
    df = df.merge(
        normalize_club_name,
        left_on="away_club",
        right_on="club_name",
        how="left"
    )
    df = df.drop(columns=["away_club", "club_name"])
    df = df.rename(columns={"club_name_normalized": "away_club"})
    logger.info("Normalized away club names")
    
    return df

def cleanse_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the attendance data using corrections from a CSV file.
    
    Args:
        df: DataFrame containing attendance data to be cleaned
        
    Returns:
        DataFrame with cleaned data
        
    Raises:
        FileNotFoundError: If the corrections file is not found
        KeyError: If required columns are missing from either DataFrame
    """

    # Remove all games for "Dover Athletic" for the 2020-2021 season
    df = df[~((df['home_club'] == 'Dover Athletic') & (df['season'] == '2020-2021'))]
    df = df[~((df['away_club'] == 'Dover Athletic') & (df['season'] == '2020-2021'))]

    # Get the current script's directory
    current_dir = Path(__file__).parent
    
    # Construct the path to the corrections file
    corrections_path = (
        current_dir / ".." / ".." / "CleansedData" / 
        "Corrections and normalization" / "attendance1_corrections.csv"
    )
    corrections_path = corrections_path.resolve()
    
    # Check if file exists
    if not corrections_path.exists():
        raise FileNotFoundError(f"Corrections file not found: {corrections_path}")
    
    # Read the corrections mapping
    corrections = pd.read_csv(corrections_path)
    logger.info("Successfully loaded attendance1 corrections mapping")
    
    # Find rows with missing match dates
    missing_dates = df[df['match_date'].isnull()]
    if not missing_dates.empty:
        logger.info(f"Found {len(missing_dates)} rows with missing match dates")
        
        # For each row with missing date, find the closest match in corrections
        for idx, row in missing_dates.iterrows():
            # Find potential matches based on home and away clubs
            potential_matches = corrections[
                (corrections['home_club'] == row['home_club']) & 
                (corrections['away_club'] == row['away_club']) &
                (corrections['season'] == row['season'])
            ]
            
            if not potential_matches.empty:
                # If there are multiple matches, log a warning and skip the fix
                if len(potential_matches) > 1:
                    logger.warning(
                        f"Found {len(potential_matches)} potential matches for "
                        f"{row['home_club']} vs {row['away_club']} in season "
                        f"{row['season']}"
                    )
                else:
                    # Get the first match (assuming corrections are ordered by relevance)
                    correction = potential_matches.iloc[0]
                    
                    # Log the change
                    logger.info(
                        f"Correcting match date for {row['home_club']} vs "
                        f"{row['away_club']}: from NULL to {correction['match_date']}"
                    )
                    
                    # Update the data in the original dataframe
                    df.iloc[idx] = correction[df.columns]
            else:
                logger.warning(
                    f"No correction found for {row['home_club']} vs {row['away_club']} "
                    f"in season {row['season']}"
                )
    
    # Remove . from attendance values
    df['attendance'] = df['attendance'].str.replace('.', '')
    
    # Replace attendance values with a null if they contain "Form" or "record" etc.
    mask = (
        df['attendance'].notna() & 
        (df['attendance'].astype(str).str.contains('Form', na=False) | 
         df['attendance'].astype(str).str.contains('record', na=False)  |
         df['attendance'].astype(str).str.contains('00k', na=False)|
         df['attendance'].astype(str).str.contains('community', na=False)|
         df['attendance'].astype(str).str.contains('play', na=False)|
         df['attendance'].astype(str).str.contains('value', na=False))
    )
    df.loc[mask, 'attendance'] = None
    
    # Replace attendance values with a null if they are "W", "L", or "D"
    mask = df['attendance'].notna() & df['attendance'].isin(['W', 'L', 'D'])
    df.loc[mask, 'attendance'] = None
    
    # Find rows with non-numeric attendance (excluding null values)
    non_numeric_attendance = df[
        df['attendance'].notna() & 
        df['attendance'].astype(str).str.contains(r'[^0-9.]', na=False)
    ]
    
    if not non_numeric_attendance.empty:
        logger.warning(f"Found {len(non_numeric_attendance)} rows with non-numeric attendance:")
        for _, row in non_numeric_attendance.iterrows():
            logger.warning(
                f"  - {row['season']} {row['league_tier']} {row['match_date']}: "
                f"{row['home_club']} vs {row['away_club']} "
                f"({row['home_goals']} - {row['away_goals']}) - "
                f"Attendance: {row['attendance']}"
            )
    
    # Find away_goals with non-numeric values and report the rows
    non_numeric_away_goals = df[
        df['away_goals'].notna() & 
        df['away_goals'].astype(str).str.contains(r'[^0-9.]', na=False)
    ]
    if not non_numeric_away_goals.empty:
        logger.warning(f"Found {len(non_numeric_away_goals)} rows with non-numeric away goals:")
        for _, row in non_numeric_away_goals.iterrows():
            logger.warning(
                f"  - {row['season']} {row['league_tier']} {row['match_date']}: "
                f"{row['home_club']} vs {row['away_club']} "
            )
    

    return df

def check_attendance1(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform data quality checks on attendance1 data.
    
    Args:
        df: DataFrame containing attendance1 data
        
    Returns:
        Dictionary containing data quality check results, including rows with null values
        
    Raises:
        ValueError: If DataFrame is empty or missing required columns
    """
    if df.empty:
        raise ValueError("DataFrame is empty")
    
    # Required columns to check
    required_columns = [
        "season", "league_tier", "match_date", 
        "home_club", "away_club", "home_goals", 
        "away_goals", "attendance"
    ]
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Initialize results dictionary
    results = {
        "null_values": {},
        "non_numeric_values": {}
    }
    
    # Check for null values in key columns
    key_columns = [
        "season", "league_tier", "match_date", 
        "home_club", "away_club", "home_goals", 
        "away_goals"
    ]
    
    for col in key_columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            # Get the rows with null values
            null_rows = df[df[col].isnull()]
            results["null_values"][col] = {
                "count": int(null_count),
                "percentage": float((null_count / len(df)) * 100),
                "rows": null_rows.to_dict('records')  # Convert to list of dicts for JSON serialization
            }
            logger.warning(f"Found {null_count} null values in {col} ({null_count/len(df)*100:.2f}%)")
            logger.warning(f"Rows with null values in {col}:")
            for _, row in null_rows.iterrows():
                logger.warning(f"  - {row.to_dict()}")
    
    # Check for non-numeric values in numeric columns
    numeric_columns = ["home_goals", "away_goals", "attendance"]
    
    for col in numeric_columns:
        # For attendance column, exclude null values from the check
        if col == "attendance":
            non_null_mask = df[col].notnull()
            non_numeric = df.loc[non_null_mask, col].astype(str).str.contains(r'[^0-9.]', na=False)
            if non_numeric.any():
                count = int(non_numeric.sum())
                results["non_numeric_values"][col] = {
                    "count": count,
                    "percentage": float((count / len(df)) * 100),
                    "examples": df.loc[non_null_mask & non_numeric, col].unique().tolist()[:5]  # Show up to 5 examples
                }
                logger.warning(f"Found {count} non-numeric values in {col} ({count/len(df)*100:.2f}%)")
                # Print all rows with non-numeric attendance
                non_numeric_rows = df.loc[non_null_mask & non_numeric]
                logger.warning("Rows with non-numeric attendance values:")
                for _, row in non_numeric_rows.iterrows():
                    logger.warning(
                        f"  - {row['season']} {row['league_tier']} {row['match_date']}: {row['home_club']} vs {row['away_club']} "
                        f"({row['home_goals']} - {row['away_goals']}) - Attendance: {row['attendance']}"
                    )
        else:
            non_numeric = df[col].astype(str).str.contains(r'[^0-9.]', na=False)
            if non_numeric.any():
                count = int(non_numeric.sum())
                results["non_numeric_values"][col] = {
                    "count": count,
                    "percentage": float((count / len(df)) * 100),
                    "examples": df.loc[non_numeric, col].unique().tolist()[:5]  # Show up to 5 examples
                }
                logger.warning(f"Found {count} non-numeric values in {col} ({count/len(df)*100:.2f}%)")
    
    return results

def save_attendance1(df: pd.DataFrame, output_path: Path) -> None:
    """Save the cleaned attendance1 data to disk.
    
    Args:
        df: DataFrame containing cleaned attendance1 data
        output_path: Path where the data should be saved
        
    Raises:
        IOError: If there are issues saving the file
    """
    try:
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the DataFrame to CSV
        df.to_csv(output_path, index=False)
        logger.info(
            f"Successfully saved attendance1 data to {output_path}"
        )
        
    except Exception as e:
        logger.error(
            f"Error saving attendance1 data to {output_path}: {str(e)}"
        )
        raise IOError(f"Failed to save attendance1 data: {str(e)}")

def main() -> None:
    """Main function to orchestrate the data cleaning process.
    
    This function:
    1. Calls read_concat_attendance1 to load the data
    2. Normalizes club names in the data
    3. Cleanses the data
    4. Performs data quality checks
    5. Handles any potential errors during the process
    """
    try:
        # Call the function to read and concatenate attendance data
        logger.info("Starting to read and concatenate attendance data")
        attendance_df = read_concat_attendance1()
        
        # Log success and basic information about the loaded data
        logger.info(
            f"Successfully loaded attendance data with {len(attendance_df)} rows"
        )
        logger.info(
            f"Columns in the dataset: {', '.join(attendance_df.columns)}"
        )
        
        # Normalize club names
        logger.info("Starting club name normalization")
        attendance_df = normalize_club_names(attendance_df)
        logger.info("Successfully normalized club names")
        
        # Cleanse data
        attendance_df = cleanse_data(attendance_df)

        # Perform data quality checks
        logger.info("Starting data quality checks")
        check_results = check_attendance1(attendance_df)
        logger.info("Completed data quality checks")
        
        # Log summary of check results
        if check_results["null_values"]:
            logger.warning("Found null values in the following columns:")
            for col, stats in check_results["null_values"].items():
                logger.warning(
                    f"  - {col}: {stats['count']} values "
                    f"({stats['percentage']:.2f}%)"
                )
        
        if check_results["non_numeric_values"]:
            logger.warning(
                "Found non-numeric values in the following columns:"
            )
            for col, stats in check_results["non_numeric_values"].items():
                logger.warning(
                    f"  - {col}: {stats['count']} values "
                    f"({stats['percentage']:.2f}%)"
                )
                logger.warning(f"    Examples: {stats['examples']}")
        
        # Save the cleaned data
        output_path = (
            Path(__file__).parent / ".." / ".." / "CleansedData" / 
            "Interim" / "attendance1.csv"
        )
        output_path = output_path.resolve()
        save_attendance1(attendance_df, output_path)
        
    except FileNotFoundError as e:
        logger.error(f"Error finding attendance data files: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error while processing attendance data: {str(e)}"
        )
        raise

if __name__ == "__main__":
    main() 