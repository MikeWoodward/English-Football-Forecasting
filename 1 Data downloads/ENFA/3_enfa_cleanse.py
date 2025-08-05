#!/usr/bin/env python3
"""Module for cleansing ENFA (English National Football Archive) data.

This module provides functions to read, cleanse, and save ENFA data from CSV
files. It handles data validation, cleaning of null values, and ensures data
integrity before saving.

The module expects data in CSV format with specific columns including match
information. The data is processed and saved in a standardized format.

Key Features:
- Reads ENFA CSV file
- Cleanses and standardizes column names
- Validates data integrity
- Handles club name transformations
- Saves processed data in a standardized format
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Add parent directory to path to import DataSourceCleanUp
# This allows access to the club name transformation utilities
sys.path.append(str(Path(__file__).parent.parent))
from DataSourceCleanUp.cleanuputilities import transform_club_names


# Configure logging with timestamp, logger name, and message
# This provides detailed logging for the data cleansing process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Mapping of league names to their tier numbers
# Used to convert league names to numerical tiers for analysis
# This mapping covers the evolution of English football leagues from 1888 to
# present
LEAGUE_TIER_MAP = pd.DataFrame([
    # ------------------------------------------------------------
    # Tier 1 - Premier League and its predecessors
    # ------------------------------------------------------------
    {
        'league_name': 'FA Premier League',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004',
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024'
        ],
        'tier': 1
    },
    {
        'league_name': 'League Division One',
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
    # ------------------------------------------------------------
    # Tier 2 - Championship and its predecessors
    # ------------------------------------------------------------
    {
        'league_name': 'Football League Championship',
        'season': [
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024'
        ],
        'tier': 2
    },
    {
        'league_name': 'League Division One',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004'
        ],
        'tier': 2
    },
    {
        'league_name': 'League Division Two',
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
    # Tier 3 - League One and its predecessors
    # ------------------------------------------------------------
    {
        'league_name': 'Football League 1',
        'season': [
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024'
        ],
        'tier': 3
    },
    {
        'league_name': 'League Division Two',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004'
        ],
        'tier': 3
    },
    {
        'league_name': 'League Division Three',
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
    # Tier 4 - League Two and its predecessors
    # ------------------------------------------------------------
    {
        'league_name': 'Football League 2',
        'season': [
            '2004-2005', '2005-2006', '2006-2007', '2007-2008',
            '2008-2009', '2009-2010', '2010-2011', '2011-2012',
            '2012-2013', '2013-2014', '2014-2015', '2015-2016',
            '2016-2017', '2017-2018', '2018-2019', '2019-2020',
            '2020-2021', '2021-2022', '2022-2023', '2023-2024'
        ],
        'tier': 4
    },
    {
        'league_name': 'League Division Three',
        'season': [
            '1992-1993', '1993-1994', '1994-1995', '1995-1996',
            '1996-1997', '1997-1998', '1998-1999', '1999-2000',
            '2000-2001', '2001-2002', '2002-2003', '2003-2004'
        ],
        'tier': 4
    },
    {
        'league_name': 'League Division Four',
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

# Season start and end dates mapping
# This maps each season to its actual start and end dates
# Mostly estimated, but filled in by hand where needed for accuracy
SEASON_START_END_MAP = pd.DataFrame([
    # Guestimates for start and end dates after this point
    {'season': '1888-1889', 'start_date': '1888-08-01', 'end_date': '1889-05-31'},
    {'season': '1889-1890', 'start_date': '1889-08-01', 'end_date': '1890-05-31'},
    {'season': '1890-1891', 'start_date': '1890-08-01', 'end_date': '1891-05-31'},
    {'season': '1891-1892', 'start_date': '1891-08-01', 'end_date': '1892-05-31'},
    {'season': '1892-1893', 'start_date': '1892-08-01', 'end_date': '1893-05-31'},
    {'season': '1893-1894', 'start_date': '1893-08-01', 'end_date': '1894-05-31'},
    {'season': '1894-1895', 'start_date': '1894-08-01', 'end_date': '1895-05-31'},
    {'season': '1895-1896', 'start_date': '1895-08-01', 'end_date': '1896-05-31'},
    {'season': '1896-1897', 'start_date': '1896-08-01', 'end_date': '1897-05-31'},
    {'season': '1897-1898', 'start_date': '1897-08-01', 'end_date': '1898-05-31'},
    {'season': '1898-1899', 'start_date': '1898-08-01', 'end_date': '1899-05-31'},
    {'season': '1899-1900', 'start_date': '1899-08-01', 'end_date': '1900-05-31'},
    {'season': '1900-1901', 'start_date': '1900-08-01', 'end_date': '1901-05-31'},
    {'season': '1901-1902', 'start_date': '1901-08-01', 'end_date': '1902-05-31'},
    {'season': '1902-1903', 'start_date': '1902-08-01', 'end_date': '1903-05-31'},
    {'season': '1903-1904', 'start_date': '1903-08-01', 'end_date': '1904-05-31'},
    {'season': '1904-1905', 'start_date': '1904-08-01', 'end_date': '1905-05-31'},
    {'season': '1905-1906', 'start_date': '1905-08-01', 'end_date': '1906-05-31'},
    {'season': '1906-1907', 'start_date': '1906-08-01', 'end_date': '1907-05-31'},
    {'season': '1907-1908', 'start_date': '1907-08-01', 'end_date': '1908-05-31'},
    {'season': '1908-1909', 'start_date': '1908-08-01', 'end_date': '1909-05-31'},
    {'season': '1909-1910', 'start_date': '1909-08-01', 'end_date': '1910-05-31'},
    {'season': '1910-1911', 'start_date': '1910-08-01', 'end_date': '1911-05-31'},
    {'season': '1911-1912', 'start_date': '1911-08-01', 'end_date': '1912-05-31'},
    {'season': '1912-1913', 'start_date': '1912-08-01', 'end_date': '1913-05-31'},
    {'season': '1913-1914', 'start_date': '1913-08-01', 'end_date': '1914-05-31'},
    {'season': '1914-1915', 'start_date': '1914-08-01', 'end_date': '1915-05-31'},
    {'season': '1919-1920', 'start_date': '1919-08-01', 'end_date': '1920-05-31'},
    {'season': '1920-1921', 'start_date': '1920-08-01', 'end_date': '1921-05-31'},
    {'season': '1921-1922', 'start_date': '1921-08-01', 'end_date': '1922-05-31'},
    {'season': '1922-1923', 'start_date': '1922-08-01', 'end_date': '1923-05-31'},
    {'season': '1923-1924', 'start_date': '1923-08-01', 'end_date': '1924-05-31'},
    {'season': '1924-1925', 'start_date': '1924-08-01', 'end_date': '1925-05-31'},
    {'season': '1925-1926', 'start_date': '1925-08-01', 'end_date': '1926-05-31'},
    {'season': '1926-1927', 'start_date': '1926-08-01', 'end_date': '1927-05-31'},
    {'season': '1927-1928', 'start_date': '1927-08-01', 'end_date': '1928-05-31'},
    {'season': '1928-1929', 'start_date': '1928-08-01', 'end_date': '1929-05-31'},
    {'season': '1929-1930', 'start_date': '1929-08-01', 'end_date': '1930-05-31'},
    {'season': '1930-1931', 'start_date': '1930-08-01', 'end_date': '1931-05-31'},
    {'season': '1931-1932', 'start_date': '1931-08-01', 'end_date': '1932-05-31'},
    {'season': '1932-1933', 'start_date': '1932-08-01', 'end_date': '1933-05-31'},
    {'season': '1933-1934', 'start_date': '1933-08-01', 'end_date': '1934-05-31'},
    {'season': '1934-1935', 'start_date': '1934-08-01', 'end_date': '1935-05-31'},
    {'season': '1935-1936', 'start_date': '1935-08-01', 'end_date': '1936-05-31'},
    {'season': '1936-1937', 'start_date': '1936-08-01', 'end_date': '1937-05-31'},
    {'season': '1937-1938', 'start_date': '1937-08-01', 'end_date': '1938-05-31'},
    {'season': '1938-1939', 'start_date': '1938-08-01', 'end_date': '1939-05-31'},
    {'season': '1946-1947', 'start_date': '1946-08-01', 'end_date': '1947-06-14'},
    {'season': '1947-1948', 'start_date': '1947-08-01', 'end_date': '1948-05-31'},
    {'season': '1948-1949', 'start_date': '1948-08-01', 'end_date': '1949-05-31'},
    {'season': '1949-1950', 'start_date': '1949-08-01', 'end_date': '1950-05-31'},
    {'season': '1950-1951', 'start_date': '1950-08-01', 'end_date': '1951-05-31'},
    {'season': '1951-1952', 'start_date': '1951-08-01', 'end_date': '1952-05-31'},
    {'season': '1952-1953', 'start_date': '1952-08-01', 'end_date': '1953-05-31'},
    {'season': '1953-1954', 'start_date': '1953-08-01', 'end_date': '1954-05-31'},
    {'season': '1954-1955', 'start_date': '1954-08-01', 'end_date': '1955-05-31'},
    {'season': '1955-1956', 'start_date': '1955-08-01', 'end_date': '1956-05-31'},
    {'season': '1956-1957', 'start_date': '1956-08-01', 'end_date': '1957-05-31'},
    {'season': '1957-1958', 'start_date': '1957-08-01', 'end_date': '1958-05-31'},
    {'season': '1958-1959', 'start_date': '1958-08-01', 'end_date': '1959-05-31'},
    {'season': '1959-1960', 'start_date': '1959-08-01', 'end_date': '1960-05-31'},
    {'season': '1960-1961', 'start_date': '1960-08-01', 'end_date': '1961-05-31'},
    {'season': '1961-1962', 'start_date': '1961-08-01', 'end_date': '1962-05-31'},
    {'season': '1962-1963', 'start_date': '1962-08-01', 'end_date': '1963-05-31'},
    {'season': '1963-1964', 'start_date': '1963-08-01', 'end_date': '1964-05-31'},
    {'season': '1964-1965', 'start_date': '1964-08-01', 'end_date': '1965-05-31'},
    {'season': '1965-1966', 'start_date': '1965-08-01', 'end_date': '1966-05-31'},
    {'season': '1966-1967', 'start_date': '1966-08-01', 'end_date': '1967-05-31'},
    {'season': '1967-1968', 'start_date': '1967-08-01', 'end_date': '1968-05-31'},
    {'season': '1968-1969', 'start_date': '1968-08-01', 'end_date': '1969-05-31'},
    {'season': '1969-1970', 'start_date': '1969-08-01', 'end_date': '1970-05-31'},
    {'season': '1970-1971', 'start_date': '1970-08-01', 'end_date': '1971-05-31'},
    {'season': '1971-1972', 'start_date': '1971-08-01', 'end_date': '1972-05-31'},
    {'season': '1972-1973', 'start_date': '1972-08-01', 'end_date': '1973-05-31'},
    {'season': '1973-1974', 'start_date': '1973-08-01', 'end_date': '1974-05-31'},
    {'season': '1974-1975', 'start_date': '1974-08-01', 'end_date': '1975-05-31'},
    {'season': '1975-1976', 'start_date': '1975-08-01', 'end_date': '1976-05-31'},
    {'season': '1976-1977', 'start_date': '1976-08-01', 'end_date': '1977-05-31'},
    {'season': '1977-1978', 'start_date': '1977-08-01', 'end_date': '1978-05-31'},
    {'season': '1978-1979', 'start_date': '1978-08-01', 'end_date': '1979-05-31'},
    {'season': '1979-1980', 'start_date': '1979-08-01', 'end_date': '1980-05-31'},
    {'season': '1980-1981', 'start_date': '1980-08-01', 'end_date': '1981-05-31'},
    {'season': '1981-1982', 'start_date': '1981-08-01', 'end_date': '1982-05-31'},
    {'season': '1982-1983', 'start_date': '1982-08-01', 'end_date': '1983-05-31'},
    {'season': '1983-1984', 'start_date': '1983-08-01', 'end_date': '1984-05-31'},
    {'season': '1984-1985', 'start_date': '1984-08-01', 'end_date': '1985-05-31'},
    {'season': '1985-1986', 'start_date': '1985-08-01', 'end_date': '1986-05-31'},
    {'season': '1986-1987', 'start_date': '1986-08-01', 'end_date': '1987-05-31'},
    {'season': '1987-1988', 'start_date': '1987-08-01', 'end_date': '1988-05-31'},
    {'season': '1988-1989', 'start_date': '1988-08-01', 'end_date': '1989-05-31'},
    {'season': '1989-1990', 'start_date': '1989-08-01', 'end_date': '1990-05-31'},
    {'season': '1990-1991', 'start_date': '1990-08-01', 'end_date': '1991-05-31'},
    {'season': '1991-1992', 'start_date': '1991-08-01', 'end_date': '1992-05-31'},
    {'season': '1992-1993', 'start_date': '1992-08-01', 'end_date': '1993-05-31'},
    {'season': '1993-1994', 'start_date': '1993-08-01', 'end_date': '1994-05-31'},
    {'season': '1994-1995', 'start_date': '1994-08-01', 'end_date': '1995-05-31'},
    {'season': '1995-1996', 'start_date': '1995-08-01', 'end_date': '1996-05-31'},
    {'season': '1996-1997', 'start_date': '1996-08-01', 'end_date': '1997-05-31'},
    {'season': '1997-1998', 'start_date': '1997-08-01', 'end_date': '1998-05-31'},
    {'season': '1998-1999', 'start_date': '1998-08-01', 'end_date': '1999-05-31'},
    {'season': '1999-2000', 'start_date': '1999-08-01', 'end_date': '2000-05-31'},
    {'season': '2000-2001', 'start_date': '2000-08-01', 'end_date': '2001-05-31'},
    {'season': '2001-2002', 'start_date': '2001-08-01', 'end_date': '2002-05-31'},
    {'season': '2002-2003', 'start_date': '2002-08-01', 'end_date': '2003-05-31'},
    {'season': '2003-2004', 'start_date': '2003-08-01', 'end_date': '2004-05-31'},
    {'season': '2004-2005', 'start_date': '2004-08-01', 'end_date': '2005-05-31'},
    {'season': '2005-2006', 'start_date': '2005-08-01', 'end_date': '2006-05-31'},
    {'season': '2006-2007', 'start_date': '2006-08-01', 'end_date': '2007-05-31'},
    {'season': '2007-2008', 'start_date': '2007-08-01', 'end_date': '2008-05-31'},
    {'season': '2008-2009', 'start_date': '2008-08-01', 'end_date': '2009-05-31'},
    {'season': '2009-2010', 'start_date': '2009-08-01', 'end_date': '2010-05-31'},
    {'season': '2010-2011', 'start_date': '2010-08-01', 'end_date': '2011-05-31'},
    {'season': '2011-2012', 'start_date': '2011-08-01', 'end_date': '2012-05-31'},
    {'season': '2012-2013', 'start_date': '2012-08-01', 'end_date': '2013-05-31'},
    {'season': '2013-2014', 'start_date': '2013-08-01', 'end_date': '2014-05-31'},
    {'season': '2014-2015', 'start_date': '2014-08-01', 'end_date': '2015-05-31'},
    {'season': '2015-2016', 'start_date': '2015-08-01', 'end_date': '2016-05-31'},
    {'season': '2016-2017', 'start_date': '2016-08-01', 'end_date': '2017-05-31'},
    {'season': '2017-2018', 'start_date': '2017-08-01', 'end_date': '2018-05-31'},
    {'season': '2018-2019', 'start_date': '2018-08-01', 'end_date': '2019-05-31'},
    # Manually entered dates below this point for accuracy
    {'season': '2019-2020', 'start_date': '2019-08-02', 'end_date': '2020-08-04'},
    {'season': '2020-2021', 'start_date': '2020-09-11', 'end_date': '2021-05-23'},
    {'season': '2021-2022', 'start_date': '2021-08-06', 'end_date': '2022-05-22'},
    {'season': '2022-2023', 'start_date': '2022-07-29', 'end_date': '2023-05-28'},
    {'season': '2023-2024', 'start_date': '2023-08-04', 'end_date': '2024-05-19'}
])

def read_data() -> pd.DataFrame:
    """Read ENFA data from CSV file.

    This function reads the ENFA CSV file and returns it as a DataFrame.
    The function performs error handling during the reading process.

    Returns:
        pd.DataFrame: DataFrame containing ENFA data.

    Raises:
        FileNotFoundError: If the data file cannot be found.
        pd.errors.EmptyDataError: If the CSV file is empty.
        Exception: For any other errors during file reading.
    """
    # Define the path to the ENFA data file
    file_path = Path("Data/enfa_baseline.csv")

    # Check if the file exists before attempting to read it
    if not file_path.exists():
        error_msg = f"ENFA data file not found: {file_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        # Read the CSV file with low_memory=False for better performance with
        # large files
        enfa = pd.read_csv(file_path, low_memory=False)
        logger.info(f"Successfully read ENFA data: {enfa.shape}")
        return enfa
    except pd.errors.EmptyDataError:
        error_msg = f"ENFA data file is empty: {file_path}"
        logger.error(error_msg)
        raise
    except Exception as e:
        error_msg = f"Error reading ENFA data file {file_path}: {str(e)}"
        logger.error(error_msg)
        raise


def get_league_tier(*, row: pd.Series) -> int:
    """Get the tier number for a given league and season.

    This function looks up the league tier based on the league name and season
    using the LEAGUE_TIER_MAP DataFrame. It handles the evolution of league
    names and structures over time.

    Args:
        row: DataFrame row containing 'season' and 'table_title' columns

    Returns:
        int: The tier number (1-4) for the league in that season

    Raises:
        ValueError: If the league tier cannot be determined
    """
    try:
        # Look up the tier in the mapping DataFrame
        tier = LEAGUE_TIER_MAP[
            (LEAGUE_TIER_MAP['season'] == row['season']) &
            (LEAGUE_TIER_MAP['league_name'] == row['table_title'])
        ]['tier'].iloc[0]
        return tier
    except (IndexError, KeyError) as e:
        msg = (
            f"Error getting league tier for season {row['season']} and league "
            f"{row['table_title']}"
        )
        print(msg)
        raise ValueError(
            f"Could not determine league tier for {row['table_title']} in "
            f"{row['season']}"
        ) from e


def get_season(*, row: pd.Series) -> str:
    """Get the season for a given match date.

    This function determines which season a match belongs to based on its date.
    It handles the fact that seasons span two calendar years and uses the
    SEASON_START_END_MAP to determine the correct season.

    Args:
        row: DataFrame row containing match_date

    Returns:
        str: The season in format 'YYYY-YYYY'

    Raises:
        ValueError: If the season cannot be determined
    """
    # Extract the year from the match date
    year = int(row['match_date'].split("-")[0])

    # The year gives us two different candidates for the season:
    # {year}-{year+1} and {year-1}-{year} depending on the season start and
    # end dates and the date of the match
    candidate_season_1 = f"{year}-{year+1}"
    candidate_season_2 = f"{year-1}-{year}"

    # Look up both candidate seasons in the mapping
    season_1 = SEASON_START_END_MAP[
        (SEASON_START_END_MAP['season'] == candidate_season_1)
    ]
    season_2 = SEASON_START_END_MAP[
        (SEASON_START_END_MAP['season'] == candidate_season_2)
    ]

    # Check if the match date falls within the first candidate season
    if (not season_1.empty and
            season_1['start_date'].iloc[0] <= row['match_date'] <=
            season_1['end_date'].iloc[0]):
        return candidate_season_1
    # Check if the match date falls within the second candidate season
    elif (not season_2.empty and
          season_2['start_date'].iloc[0] <= row['match_date'] <=
          season_2['end_date'].iloc[0]):
        return candidate_season_2
    else:
        msg = f"Could not determine season for match date {row['match_date']}"
        print(msg)
        raise ValueError(msg)


def cleanse_data(enfa: pd.DataFrame) -> pd.DataFrame:
    """Clean and preprocess the ENFA data.

    This function performs comprehensive data cleaning operations including:
    1. Renaming columns for consistency
    2. Adding season and league tier information
    3. Transforming club names to standardized format
    4. Applying data corrections
    5. Adding missing data for recent seasons
    6. Ensuring data types are correct
    7. Sorting the data for consistency

    Args:
        enfa (pd.DataFrame): Raw ENFA data to be cleansed.

    Returns:
        pd.DataFrame: Cleansed ENFA data ready for analysis.

    Raises:
        ValueError: If club name transformation fails.
    """
    # Rename match_day column to match_day_of_week for consistency
    enfa = enfa.rename(columns={'match_day': 'match_day_of_week'})
    logger.info("Renamed 'match_day' column to 'match_day_of_week'")

    # Work out the season from the match date
    # This must be called before the league tier is calculated as it depends
    # on season
    enfa['season'] = enfa.apply(
        lambda row: get_season(row=row), axis=1
    )

    # Get the league tier from the mapping and season
    # This converts league names to numerical tiers (1-4) for analysis
    enfa['league_tier'] = enfa.apply(
        lambda row: get_league_tier(row=row), axis=1
    )

    # Transform home club names to standardized format
    # This ensures consistent club names across the dataset
    enfa = transform_club_names(
        df=enfa,
        source_name="home_club",
        target_name="home_club",
        logger=logger
    )

    # Transform away club names to standardized format
    enfa = transform_club_names(
        df=enfa,
        source_name="away_club",
        target_name="away_club",
        logger=logger
    )

    # Remove unneeded columns - table_title is no longer needed after tier
    # mapping
    enfa = enfa.drop(columns=['table_title'])

    # Apply corrections to the data
    # Read in known corrections from the Corrections directory
    corrections = pd.read_csv("Corrections/enfa_corrections.csv",
                             low_memory=False)

    # Remove known wrong results from the dataset
    enfa = enfa[~((enfa['match_date'] == '1894-02-03') &
                   (enfa['home_club'] == 'Grimsby Town') &
                   (enfa['away_club'] == 'Middlesbrough Ironopolis'))]

    # Replace with correct data by concatenating corrections
    enfa = pd.concat([corrections, enfa])

    # Read in missing 2024-2025 season data from separate files
    # This data is stored by tier for easier management
    tier_1 = pd.read_csv("Corrections/1_2024-2025.csv", low_memory=False)
    tier_2 = pd.read_csv("Corrections/2_2024-2025.csv", low_memory=False)
    tier_3 = pd.read_csv("Corrections/3_2024-2025.csv", low_memory=False)
    tier_4 = pd.read_csv("Corrections/4_2024-2025.csv", low_memory=False)

    # Combine all missing tier data
    missing_tiers = pd.concat([tier_1, tier_2, tier_3, tier_4])

    # Add day of week information for the missing data
    missing_tiers['match_day_of_week'] = (
        pd.to_datetime(missing_tiers['match_date']).dt.day_name()
    )

    # Transform club names in the missing data to match the main dataset
    missing_tiers = transform_club_names(
        df=missing_tiers,
        source_name="home_club",
        target_name="home_club",
        logger=logger
    )
    missing_tiers = transform_club_names(
        df=missing_tiers,
        source_name="away_club",
        target_name="away_club",
        logger=logger
    )

    # Add the missing tiers to the main dataset
    enfa = pd.concat([enfa, missing_tiers])

    # Ensure goal columns are integers for consistency
    enfa['home_goals'] = enfa['home_goals'].astype(int)
    enfa['away_goals'] = enfa['away_goals'].astype(int)

    # Sort the data by season, league tier, match date, and home club
    # This ensures consistent ordering for analysis
    enfa = enfa.sort_values(by=['season', 'league_tier', 'match_date',
                                'home_club'])

    logger.info("ENFA data cleansing completed successfully")
    return enfa


def save_data(
    enfa: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """Save the cleansed ENFA data to disk.

    This function saves the processed DataFrame to a CSV file. If no output
    path is specified, it uses a default path in the Data directory.
    The function creates any necessary directories in the path.

    Args:
        enfa (pd.DataFrame): Cleansed ENFA data to save.
        output_path (Optional[Path]): Path where the data should be saved.
            If None, defaults to 'Data/enfa_cleansed.csv'.

    Raises:
        IOError: If there are any issues creating directories or writing the
        file.
    """
    if output_path is None:
        output_path = Path("Data/enfa_cleansed.csv")

    try:
        # Create output directory structure if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save DataFrame to CSV without index column for cleaner output
        enfa.to_csv(output_path, index=False)
        logger.info(f"Successfully saved cleansed ENFA data to {output_path}")
    except Exception as e:
        error_msg = f"Error saving ENFA data to {output_path}: {str(e)}"
        logger.error(error_msg)
        raise IOError(error_msg)


if __name__ == "__main__":
    try:
        logger.info("Starting ENFA data cleansing process")

        # Read the raw data from the baseline CSV file
        enfa = read_data()

        # Cleanse the data using the comprehensive cleaning function
        enfa = cleanse_data(enfa)

        # Save the cleansed data to the output file
        save_data(enfa)

        logger.info("ENFA data cleansing process completed successfully")

    except Exception as e:
        logger.error(f"ENFA data cleansing process failed: {str(e)}")
        raise 