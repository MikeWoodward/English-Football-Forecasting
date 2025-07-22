#!/usr/bin/env python3
"""
Cleanse English Football League Tables Matches Data.

This module provides functions to read, merge, cleanse, and save English
football league tables matches data from CSV files.
"""

import logging
import os
import sys
from pathlib import Path

import pandas as pd

# Add parent directory to path to import DataSourceCleanUp
sys.path.append(str(Path(__file__).parent.parent))
from DataSourceCleanUp.cleanuputilities import transform_club_names

# Mapping of league names to their tier numbers
# Used to convert league names to numerical tiers for analysis
LEAGUE_TIER_MAP = pd.DataFrame([
    # ------------------------------------------------------------
    # Tier 1
    # ------------------------------------------------------------
    {
        'league_name': 'Premier League',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004',
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024',
            '2024-2025'
        ],
        'tier': 1
    },
    {
        'league_name': 'Division 1',
        'season': [
            '1892-1893', '1893-1894', '1894-1895', '1895-1896',
            '1896-1897', '1897-1898', '1898-1899', '1899-1900',
            '1900-1901', '1901-1902', '1902-1903', '1903-1904',
            '1904-1905', '1905-1906', '1906-1907', '1907-1908',
            '1908-1909', '1909-1910', '1910-1911', '1911-1912',
            '1912-1913', '1913-1914', '1914-1915', '1919-1920',
            '1920-1921', '1921-1922', '1922-1923', '1923-1924',
            '1924-1925', '1925-1926', '1926-1927', '1927-1928',
            '1928-1929', '1929-1930', '1930-1931', '1931-1932',
            '1932-1933', '1933-1934', '1934-1935', '1935-1936',
            '1936-1937', '1937-1938', '1938-1939', '1946-1947',
            '1947-1948', '1948-1949', '1949-1950', '1950-1951',
            '1951-1952', '1952-1953', '1953-1954', '1954-1955',
            '1955-1956', '1956-1957', '1957-1958', '1958-1959',
            '1959-1960', '1960-1961', '1961-1962', '1962-1963',
            '1963-1964', '1964-1965', '1965-1966', '1966-1967',
            '1967-1968', '1968-1969', '1969-1970', '1970-1971',
            '1971-1972', '1972-1973', '1973-1974', '1974-1975',
            '1975-1976', '1976-1977', '1977-1978', '1978-1979',
            '1979-1980', '1980-1981', '1981-1982', '1982-1983',
            '1983-1984', '1984-1985', '1985-1986', '1986-1987',
            '1987-1988', '1988-1989', '1989-1990', '1990-1991',
            '1991-1992'
        ],
        'tier': 1
    },
    {
        'league_name': 'Football League',
        'season': [
            '1891-1892', '1890-1891', '1889-1890', '1888-1889'
        ],
        'tier': 1
    },
    {
        'league_name': 'First Division',
        'season': [
            '1898-1899', '1977-1978', '1978-1979'
        ],
        'tier': 1
    },
    # ------------------------------------------------------------
    # Tier 2
    # ------------------------------------------------------------
    {
        'league_name': 'Championship',
        'season': [
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024',
            '2024-2025'
        ],
        'tier': 2
    },
    {
        'league_name': 'First Division',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004',
            '2021-2022'
        ],
        'tier': 2
    },
    {
        'league_name': 'Division 1',
        'season': [
            '1992-1993'
        ],
        'tier': 2
    },
    {
        'league_name': 'Second Division',
        'season': [
            '1892-1893', '1893-1894', '1894-1895', '1895-1896',
            '1896-1897', '1897-1898', '1898-1899', '1899-1900',
            '1900-1901', '1901-1902', '1902-1903', '1903-1904',
            '1904-1905', '1905-1906', '1906-1907', '1907-1908',
            '1908-1909', '1909-1910', '1910-1911', '1911-1912',
            '1912-1913', '1913-1914', '1914-1915', '1919-1920',
            '1920-1921', '1921-1922', '1922-1923', '1923-1924',
            '1924-1925', '1925-1926', '1926-1927', '1927-1928',
            '1928-1929', '1929-1930', '1930-1931', '1931-1932',
            '1932-1933', '1933-1934', '1934-1935', '1935-1936',
            '1936-1937', '1937-1938', '1938-1939', '1946-1947',
            '1947-1948', '1948-1949', '1949-1950', '1950-1951',
            '1951-1952', '1952-1953', '1953-1954', '1954-1955',
            '1955-1956', '1956-1957', '1957-1958', '1958-1959',
            '1959-1960', '1960-1961', '1961-1962', '1962-1963',
            '1963-1964', '1964-1965', '1965-1966', '1966-1967',
            '1967-1968', '1968-1969', '1969-1970', '1970-1971',
            '1971-1972', '1972-1973', '1973-1974', '1974-1975',
            '1975-1976', '1976-1977', '1977-1978', '1978-1979',
            '1979-1980', '1980-1981', '1981-1982', '1982-1983',
            '1983-1984', '1984-1985', '1985-1986', '1986-1987',
            '1987-1988', '1988-1989', '1989-1990', '1990-1991',
            '1991-1992'
        ],
        'tier': 2
    },
    # ------------------------------------------------------------
    # Tier 3
    # ------------------------------------------------------------
    {
        'league_name': 'League One',
        'season': [
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024',
            '2024-2025'
        ],
        'tier': 3
    },
    {
        'league_name': 'Second Division',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004'
        ],
        'tier': 3
    },
    {
        'league_name': 'Division 3',
        'season': [
            '1965-1966'
        ],
        'tier': 3
    },
    {
        'league_name': 'Third Division',
        'season': [
            '1958-1959', '1959-1960', '1960-1961', '1961-1962',
            '1962-1963', '1963-1964', '1964-1965', '1965-1966',
            '1966-1967', '1967-1968', '1968-1969', '1969-1970',
            '1970-1971', '1971-1972', '1972-1973', '1973-1974',
            '1974-1975', '1975-1976', '1976-1977', '1977-1978',
            '1978-1979', '1979-1980', '1980-1981', '1981-1982',
            '1982-1983', '1983-1984', '1984-1985', '1985-1986',
            '1986-1987', '1987-1988', '1988-1989', '1989-1990',
            '1990-1991', '1991-1992'
        ],
        'tier': 3
    },
    # ------------------------------------------------------------
    # Tier 4
    # ------------------------------------------------------------
    {
        'league_name': 'League Two',
        'season': [
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024',
            '2024-2025'
        ],
        'tier': 4
    },
    {
        'league_name': 'Third Division',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004'
        ],
        'tier': 4
    },
    {
        'league_name': 'Division 4',
        'season': [
            '1965-1966', '1979-1980'
        ],
        'tier': 4
    },
    {
        'league_name': 'Fourth Division',
        'season': [
            '1958-1959', '1959-1960', '1960-1961', '1961-1962',
            '1962-1963', '1963-1964', '1964-1965', '1965-1966',
            '1966-1967', '1967-1968', '1968-1969', '1969-1970',
            '1970-1971', '1971-1972', '1972-1973', '1973-1974',
            '1974-1975', '1975-1976', '1976-1977', '1977-1978',
            '1978-1979', '1979-1980', '1980-1981', '1981-1982',
            '1982-1983', '1983-1984', '1984-1985', '1985-1986',
            '1986-1987', '1987-1988', '1988-1989', '1989-1990',
            '1990-1991', '1991-1992'
        ],
        'tier': 4
    },
]).explode('season')


def setup_logging() -> None:
    """Set up logging configuration for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(
                'cleanse_englishfootballleaguetables_matches.log'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )


def read_merge_files(*, data_in_folder: str) -> pd.DataFrame:
    """
    Read and merge CSV files with pattern
    englishfootballleaguetables_matches*.csv.

    Args:
        data_in_folder: Path to the folder containing input CSV files.

    Returns:
        pd.DataFrame: Merged dataframe from all matching CSV files.

    Raises:
        FileNotFoundError: If the input folder doesn't exist.
        ValueError: If no matching CSV files are found.
    """
    try:
        input_path = Path(data_in_folder)
        if not input_path.exists():
            raise FileNotFoundError(
                f"Input folder not found: {data_in_folder}"
            )

        # Find all CSV files matching the pattern
        pattern = "englishfootballleaguetables_matches*.csv"
        csv_files = list(input_path.glob(pattern))

        if not csv_files:
            raise ValueError(
                f"No CSV files found matching pattern '{pattern}' in "
                f"{data_in_folder}"
            )

        logging.info(f"Found {len(csv_files)} CSV files to merge")

        # Read and concatenate all CSV files
        dataframes = []
        for csv_file in csv_files:
            logging.info(f"Reading file: {csv_file.name}")
            try:
                df = pd.read_csv(csv_file, low_memory=False)
                dataframes.append(df)
                logging.info(
                    f"Successfully read {len(df)} rows from {csv_file.name}"
                )
            except Exception as e:
                logging.error(f"Error reading {csv_file.name}: {e}")
                raise

        # Concatenate all dataframes
        merged_df = pd.concat(dataframes, ignore_index=True)
        logging.info(f"Successfully merged {len(merged_df)} total rows")

        return merged_df

    except Exception as e:
        logging.error(
            f"Error in read_merge_files at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise


def get_league_tier(*, row: pd.Series) -> int:
    """Get the tier number for a given league and season.

    Args:
        row: pandas Series containing 'season' and 'table_title' columns

    Returns:
        int: The tier number (1-4) for the league in that season

    Raises:
        ValueError: If the league tier cannot be determined
        KeyError: If required columns are missing from the row
        TypeError: If row data types are incorrect
        AttributeError: If LEAGUE_TIER_MAP is not properly initialized
    """
    try:
        # Filter the mapping dataframe
        filtered_map = LEAGUE_TIER_MAP[
            (LEAGUE_TIER_MAP['season'] == row['season']) &
            (LEAGUE_TIER_MAP['league_name'] == row['league_name'])
        ]

        # Check if any matches were found
        if filtered_map.empty:
            raise ValueError(
                f"No league tier mapping found for season "
                f"'{row['season']}' and league '{row['league_name']}'"
            )

        # Get the tier value
        tier = int(filtered_map['tier'].iloc[0])

        # Validate tier is a valid integer
        if tier not in [1, 2, 3, 4]:
            raise ValueError(f"Invalid tier value: {tier}")

        return int(tier)

    except (IndexError, KeyError, TypeError, AttributeError, ValueError) as e:
        logging.error(
            f"Error getting league tier for season "
            f"'{row.get('season', 'N/A')}' "
            f"and league '{row.get('table_title', 'N/A')}': {e}"
        )
        raise ValueError(
            f"Could not determine league tier for "
            f"'{row.get('table_title', 'N/A')}' "
            f"in '{row.get('season', 'N/A')}': {e}"
        ) from e


def cleanse_data(*, matches_dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Cleanse the matches dataframe by removing duplicates and sorting.

    Args:
        matches_dataframe: Input dataframe to be cleansed.

    Returns:
        pd.DataFrame: Cleansed dataframe with duplicates removed and sorted.
    """
    try:
        logging.info(
            f"Starting data cleansing on {len(matches_dataframe)} rows"
        )

        # Remove duplicates
        matches_dataframe = matches_dataframe.drop_duplicates()

        # Remove the league_names "Third Division South" and "Third Division North"
        matches_dataframe = matches_dataframe[
            ~matches_dataframe['league_name'].isin([
                'Third Division South', 'Third Division North'
            ])
        ]

        # Correct the season
        matches_dataframe['season'] = matches_dataframe['season'].apply(
            lambda row: f"{int(row[0:4])}-{int(row[0:4]) + 1}"
        )

        # Remove league_name "Third Division" that occurs in 1920-1921
        matches_dataframe = matches_dataframe[
            ~((
                matches_dataframe['league_name'] == 'Third Division'
            ) & (matches_dataframe['season'] == '1920-1921'))
        ]

        # Remove the 1939-1940 season
        matches_dataframe = matches_dataframe[
            ~(matches_dataframe['season'] == '1939-1940')
        ]

        # Add league_tier column based on league_name
        matches_dataframe['league_tier'] = matches_dataframe.apply(
            lambda row: get_league_tier(row=row),
            axis=1
        )

        # Remove rows where the club names are null
        matches_dataframe = matches_dataframe[
            ~matches_dataframe['home_team'].isnull()
        ]
        matches_dataframe = matches_dataframe[
            ~matches_dataframe['away_team'].isnull()
        ]

        # Correct the home_team name and away_team name
        matches_dataframe = transform_club_names(
            df=matches_dataframe,
            source_name="home_team",
            target_name="home_club",
            logger=logging
        )
        matches_dataframe = transform_club_names(
            df=matches_dataframe,
            source_name="away_team",
            target_name="away_club",
            logger=logging
        )

        # Rename "date" to "match_date", "home_score" to "home_goals",
        # "away_score" to "away_goals"
        matches_dataframe = matches_dataframe.rename(
            columns={
                'date': 'match_date',
                'home_score': 'home_goals',
                'away_score': 'away_goals'
            }
        )

        # Create a day of week column from the match_date
        matches_dataframe['match_day_of_week'] = (
            pd.to_datetime(matches_dataframe['match_date']).dt.day_name()
        )

        # Remove league_name column
        matches_dataframe = matches_dataframe.drop(columns=['league_name'])

        # Remove "Aldershot Town" for the season "1991-1992" - they were
        # removed by football authorities
        matches_dataframe = matches_dataframe[
            ~((matches_dataframe['home_club'] == 'Aldershot Town') &
              (matches_dataframe['season'] == '1991-1992'))
        ]
        matches_dataframe = matches_dataframe[
            ~((matches_dataframe['away_club'] == 'Aldershot Town') &
              (matches_dataframe['season'] == '1991-1992'))
        ]
        # Remove "Accrington Stanley" for the season 1961-1962 because of bankruptcy
        matches_dataframe = matches_dataframe[
            ~((matches_dataframe['home_club'] == 'Accrington Stanley') &
              (matches_dataframe['season'] == '1961-1962'))
        ]
        matches_dataframe = matches_dataframe[
            ~((matches_dataframe['away_club'] == 'Accrington Stanley') &
              (matches_dataframe['season'] == '1961-1962'))
        ]

        # Sort by season, league_tier, match_date, and home_club
        matches_dataframe = matches_dataframe.sort_values(
            ['season', 'league_tier', 'match_date', 'home_club']
        ).reset_index(drop=True)

        logging.info(
            "Data cleansing completed. Final dataset has "
            f"{len(matches_dataframe)} rows"
        )

        return matches_dataframe

    except Exception as e:
        logging.error(
            "Error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise


def save_data(*, matches_dataframe: pd.DataFrame, data_out_folder: str) -> None:
    """
    Save the matches dataframe to a CSV file.

    Args:
        matches_dataframe: Dataframe to save.
        data_out_folder: Path to the output folder.

    Raises:
        FileNotFoundError: If the output folder doesn't exist.
        PermissionError: If there's no permission to write to the folder.
    """
    try:
        output_path = Path(data_out_folder)
        if not output_path.exists():
            logging.info(f"Creating output directory: {data_out_folder}")
            output_path.mkdir(parents=True, exist_ok=True)

        output_file = os.path.join(output_path, "englishfootballleaguetables_matches.csv")

        logging.info(f"Saving data to: {output_file}")
        matches_dataframe.to_csv(output_file, index=False)

        logging.info(
            f"Successfully saved {len(matches_dataframe)} rows to "
            f"{output_file}"
        )

    except Exception as e:
        logging.error(
            f"Error in save_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise


if __name__ == "__main__":
    """Main function to execute the data cleansing pipeline."""
    try:
        setup_logging()
        logging.info(
            "Starting English Football League Tables matches data cleansing"
        )

        # Define input and output paths
        data_in_folder = "Data"
        data_out_folder = "Data"

        # Execute the pipeline
        logging.info("Step 1: Reading and merging CSV files")
        matches_df = read_merge_files(data_in_folder=data_in_folder)

        logging.info("Step 2: Cleansing data")
        cleansed_df = cleanse_data(matches_dataframe=matches_df)

        logging.info("Step 3: Saving cleansed data")
        save_data(
            matches_dataframe=cleansed_df,
            data_out_folder=data_out_folder
        )

        logging.info(
            "Data cleansing pipeline completed successfully"
        )

    except Exception as e:
        logging.error(
            "Pipeline failed at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        sys.exit(1) 