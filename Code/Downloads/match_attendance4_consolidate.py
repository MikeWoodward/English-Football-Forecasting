"""Script to consolidate attendance data from multiple CSV files.

This script provides functionality to read and combine attendance data
from multiple CSV files into a single consolidated dataset.
"""

import pandas as pd
from pathlib import Path
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


def read_attendance4s(
    directory: str = "../../RawData/Matches/Attendance4"
) -> List[pd.DataFrame]:
    """Read all CSV files from the specified directory into a list of DataFrames.

    Args:
        directory: Path to the directory containing attendance CSV files.

    Returns:
        List[pd.DataFrame]: List of DataFrames containing attendance data.

    Raises:
        FileNotFoundError: If the specified directory does not exist.
    """
    # Convert directory to Path object
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # List to store individual dataframes
    dfs: List[pd.DataFrame] = []
    
    logging.info("Loading CSV files from directory: %s", directory)
    
    # Read each CSV file in the directory
    for file in dir_path.glob("*.csv"):
        if file.name != ".DS_Store":  # Skip system files
            try:
                logging.info("\nProcessing file: %s", file.name)
                
                # First, read the file without date parsing to check for blank dates
                df_temp = pd.read_csv(file, low_memory=False)
                
                # Check for blank or missing match_date values
                if 'match_date' in df_temp.columns:
                    # Count completely empty values
                    empty_dates = df_temp['match_date'].isna().sum()
                    # Count whitespace-only values
                    whitespace_dates = df_temp[
                        df_temp['match_date'].astype(str).str.strip() == ''
                    ].shape[0]
                    
                    if empty_dates > 0 or whitespace_dates > 0:
                        logging.warning("Match date issues found:")
                        if empty_dates > 0:
                            logging.warning(
                                "  - Empty values: %d (%.2f%%)",
                                empty_dates,
                                (empty_dates / len(df_temp)) * 100
                            )
                        if whitespace_dates > 0:
                            logging.warning(
                                "  - Whitespace-only values: %d (%.2f%%)",
                                whitespace_dates,
                                (whitespace_dates / len(df_temp)) * 100
                            )
                        
                        # Show sample of rows with blank dates
                        blank_dates_df = df_temp[
                            df_temp['match_date'].isna() |
                            (df_temp['match_date'].astype(str).str.strip() == '')
                        ]
                        if not blank_dates_df.empty:
                            logging.warning("\nSample of rows with blank dates:")
                            sample_size = min(5, len(blank_dates_df))
                            logging.warning(
                                blank_dates_df.head(sample_size).to_string()
                            )
                
                # Check the date format in the first few rows
                date_format = None
                if 'match_date' in df_temp.columns:
                    sample_dates = df_temp['match_date'].head()
                    if all(pd.to_datetime(sample_dates, errors='coerce').notna()):
                        date_format = '%Y-%m-%d'
                    else:
                        # Try European format
                        try:
                            pd.to_datetime(sample_dates, format='%d/%m/%Y')
                            date_format = '%d/%m/%Y'
                        except:
                            pass
                
                # Now read the file with the appropriate date format
                df = pd.read_csv(
                    file,
                    low_memory=False,
                    parse_dates=['match_date'],
                    date_format=date_format
                )
                
                # Report basic information about the DataFrame
                logging.info("\nDataFrame Information:")
                logging.info("Number of rows: %d", len(df))
                logging.info("Columns: %s", list(df.columns))
                
                # Check for missing values
                missing_values = df.isnull().sum()
                if missing_values.any():
                    logging.info("\nMissing values by column:")
                    for col, count in missing_values[missing_values > 0].items():
                        logging.info(
                            "  %s: %d (%.2f%%)",
                            col,
                            count,
                            (count / len(df)) * 100
                        )
                
                # Check date column for potential issues
                if 'match_date' in df.columns:
                    date_issues = df['match_date'].isnull().sum()
                    if date_issues > 0:
                        logging.warning("\nDate parsing issues:")
                        logging.warning(
                            "  - Failed to parse: %d rows (%.2f%%)",
                            date_issues,
                            (date_issues / len(df)) * 100
                        )
                    
                    # Check for invalid dates
                    if df['match_date'].dtype == 'datetime64[ns]':
                        invalid_dates = df[df['match_date'].dt.year < 1900]
                        if len(invalid_dates) > 0:
                            logging.warning(
                                "  - Dates before 1900: %d rows (%.2f%%)",
                                len(invalid_dates),
                                (len(invalid_dates) / len(df)) * 100
                            )
                
                dfs.append(df)
                
            except Exception as e:
                logging.error("Error processing file %s: %s", file.name, str(e))
                continue
    
    logging.info("\nSuccessfully loaded %d files", len(dfs))
    return dfs


def combine_attendance4s(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """Combine multiple attendance DataFrames into a single consolidated DataFrame.

    Args:
        dfs: List of DataFrames to combine.

    Returns:
        pd.DataFrame: Consolidated DataFrame containing all attendance data.
    """
    # Report number of rows in each DataFrame
    logging.info("\nRows in each DataFrame before combining:")
    total_input_rows = 0
    for i, df in enumerate(dfs, 1):
        logging.info(f"DataFrame {i}: {len(df):,} rows")
        total_input_rows += len(df)
    logging.info(f"Total rows across all DataFrames: {total_input_rows:,}")
    
    # Combine all DataFrames
    attendance4 = pd.concat(dfs, ignore_index=True)
    logging.info(f"\nRows in combined DataFrame: {len(attendance4):,}")
    
    # Drop duplicates and report
    rows_before = len(attendance4)
    attendance4 = attendance4.drop_duplicates()
    rows_after = len(attendance4)
    rows_dropped = rows_before - rows_after
    
    logging.info("\nDuplicate removal summary:")
    logging.info(f"Rows before deduplication: {rows_before:,}")
    logging.info(f"Rows after deduplication: {rows_after:,}")
    logging.info(f"Duplicate rows removed: {rows_dropped:,}")
    if rows_before > 0:
        logging.info(
            f"Percentage of duplicates: {(rows_dropped/rows_before)*100:.2f}%"
        )
    
    return attendance4


def main() -> None:
    """Main function to execute the attendance data consolidation."""
    try:
        # Read the attendance data
        dfs = read_attendance4s()
        
        # Combine the DataFrames
        consolidated_df = combine_attendance4s(dfs)

        # Order the dataframe by season, league_tier, match_date, home_club
        consolidated_df = consolidated_df.sort_values(
            by=['season', 'league_tier', 'match_date', 'home_club']
        )
        
        # Save the consolidated DataFrame to CSV
        output_path = Path("../../RawData/Matches/Attendance4/attendance4.csv")
        consolidated_df.to_csv(output_path, index=False)
        logging.info(f"\nSaved consolidated data to: {output_path}")
        
    except FileNotFoundError as e:
        logging.error("Error: %s", e)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    main() 