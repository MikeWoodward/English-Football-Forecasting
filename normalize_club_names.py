"""
club_name_normalization.py - Club Name Normalization Script

This script reads club names from various data sources, removes duplicates,
and creates a normalization mapping for consistent club name usage across datasets.

The script:
1. Reads CSV files from multiple data source folders
2. Extracts club names from each source
3. Combines and deduplicates club names
4. Creates a normalization mapping
5. Saves the mapping to a CSV file for reference

Author: Mike Woodward
Date: April 2024
"""

import os
import pandas as pd
import glob

def get_csv_files(base_path, folder):
    """
    Get all CSV files from a specific folder in the RawData directory.
    
    Args:
        base_path (str): Path to the RawData directory
        folder (str): Name of the subfolder to search
        
    Returns:
        list: List of CSV file paths
    """
    search_path = os.path.join(base_path, folder, "*.csv")
    return glob.glob(search_path)

def extract_club_names(file_path):
    """
    Extract club names from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        set: Set of unique club names found in the file
    """
    try:
        df = pd.read_csv(file_path)
        club_names = set()
        
        # Common column names for club names across different data sources
        possible_columns = [
            'home team', 'away team',  # Attendance data
            'HomeTeam', 'AwayTeam',    # Football-data
            'Team',                    # TransferValues
            'Home', 'Away'            # FBRef
        ]
        
        # Extract club names from relevant columns
        for col in possible_columns:
            if col in df.columns:
                club_names.update(df[col].dropna().unique())
        
        return club_names
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return set()

def main():
    """
    Main function to process club names and create normalization mapping.
    """
    # Define paths
    raw_data_path = "../../RawData"
    output_path = "../../CleansedData/Normalization"
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Source folders to process - updated paths to match actual directory structure
    folders = [
        'Matches/TransferValues', 
        'Matches/Football-data', 
        'Matches/FBRef', 
        'Matches/Attendance'
    ]
    
    # Collect all unique club names
    all_club_names = set()
    
    # Process each folder
    for folder in folders:
        print(f"Processing files in {folder}...")
        csv_files = get_csv_files(raw_data_path, folder)
        
        print(f"Found {len(csv_files)} CSV files")
        
        for file in csv_files:
            club_names = extract_club_names(file)
            all_club_names.update(club_names)
    
    # Create sorted list of unique club names
    sorted_names = sorted(list(all_club_names))
    
    # Create DataFrame with original and normalized names
    df_normalization = pd.DataFrame({
        'club_name': sorted_names,
        'normalized_club_name': sorted_names
    })
    
    # Save to CSV
    output_file = os.path.join(output_path, 'club_name_normalization.csv')
    df_normalization.to_csv(output_file, index=False)
    print(f"\nNormalization mapping saved to: {output_file}")
    print(f"Total unique club names found: {len(sorted_names)}")

if __name__ == "__main__":
    main() 