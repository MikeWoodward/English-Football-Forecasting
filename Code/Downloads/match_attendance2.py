"""
match_attendance2.py - Football Attendance Data Downloader

This script downloads football attendance data from footballwebpages.co.uk by:
1. Constructing URLs for each season's data
2. Downloading CSV files
3. Saving files to the specified folder with formatted filenames (YYYY-YYYY.csv)

Author: Mike Woodward
Date: April 2024
"""

import os
import time
import sys
from pathlib import Path

# Check for required packages
try:
    import requests
except ImportError:
    print("Error: The 'requests' package is required. Please install it using:")
    print("pip install requests")
    sys.exit(1)

def create_output_directory():
    """
    Create the output directory if it doesn't exist.
    
    Returns:
        str: Path to the output directory
    """
    # Get the user's home directory
    home_dir = str(Path.home())
    
    # Construct the full path
    project_root = os.path.join(home_dir, 'Documents', 'Projects', 'Python', 'EPL predictor')
    output_dir = os.path.join(project_root, 'RawData', 'Matches', 'Attendance2')
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Files will be saved to: {output_dir}")
    return output_dir

def download_file(url, output_path):
    """
    Download a file from a URL and save it to the specified path.
    
    Args:
        url (str): URL to download from
        output_path (str): Path to save the file to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_attendance_data():
    """
    Download attendance data from footballwebpages.co.uk.
    """
    base_url = "https://www.footballwebpages.co.uk/archive.csv?season={filename}"
    filenames = [
        "20222023.csv", "20212022.csv", "20202021.csv", "20192020.csv",
        "20182019.csv", "20172018.csv", "20162017.csv", "20152016.csv",
        "20142015.csv", "20132014.csv", "20122013.csv", "20112012.csv",
        "20102011.csv", "20092010.csv", "20082009.csv", "20072008.csv",
        "20062007.csv", "20052006.csv", "20042005.csv"
    ]
    
    output_dir = create_output_directory()
    
    print(f"\nFound {len(filenames)} seasons to download")
    
    # Download each file
    successful_downloads = 0
    for i, filename in enumerate(filenames, 1):
        # Construct URL using original filename format
        url = base_url.format(filename=filename.replace('.csv', ''))
        
        # Transform filename to include hyphen (e.g., 2022-2023.csv)
        formatted_filename = f"{filename[:4]}-{filename[4:8]}.csv"
        output_path = os.path.join(output_dir, formatted_filename)
        
        print(f"\nDownloading file {i} of {len(filenames)}: {formatted_filename}")
        print(f"URL: {url}")
        
        if download_file(url, output_path):
            print(f"Successfully downloaded {formatted_filename}")
            successful_downloads += 1
        else:
            print(f"Failed to download {formatted_filename}")
        
        # Add a small delay between downloads to be polite
        time.sleep(1)
    
    print(f"\nDownload process completed! Successfully downloaded {successful_downloads} of {len(filenames)} files")

def main():
    """
    Main function to orchestrate the download process.
    """
    try:
        print("Starting attendance data download...")
        download_attendance_data()
        print("\nProcess completed successfully!")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 