# Football Data Collection Project

This project collects football match data from various sources to create a comprehensive dataset for analysis. All data collection is done with respect for the source websites, implementing appropriate delays between requests and proper error handling.

## Data Sources

### 1. FBRef.com
**Service Description**: Professional football statistics and match data provider
**Data Extracted**:
- Match schedules and results
- League standings
- Historical match data from 1888 onwards
**Files Using This Service**:
- `FBRef.py`
**Rate Limiting**: Implements 30-60 second random delays between requests

### 2. Transfermarkt
**Service Description**: Football transfer market and team statistics website
**Data Extracted**:
- Team market values
- Squad information
- Player statistics
**Files Using This Service**:
- `TransferValue.py`
- `match_attendance1.py`
**Rate Limiting**: Implements 2-4 second random delays between requests

### 3. Football-data.co.uk
**Service Description**: Historical football match data provider
**Data Extracted**:
- Match results
- League tables
- Historical data from 1993 onwards
**Files Using This Service**:
- `FootballData.py`
**Rate Limiting**: Implements 60-120 second random delays between requests

### 4. Todor66.com
**Service Description**: Historical football match data archive
**Data Extracted**:
- National League match data
- Historical data from 1979-80 to 1997-98
**Files Using This Service**:
- `todor.py`
**Rate Limiting**: Implements 10 second delays between requests

### 5. FootballWebPages.co.uk
**Service Description**: Football statistics and attendance data provider
**Data Extracted**:
- Match attendance figures
- Competition data
**Files Using This Service**:
- `match_attendance2.py`
**Rate Limiting**: Implements appropriate delays between requests

### 6. GitHub (engsoccerdata)
**Service Description**: Open-source football data repository
**Data Extracted**:
- Historical match data
- League tables
**Files Using This Service**:
- `match_attendance5.py`
**Rate Limiting**: Standard GitHub API rate limits

## Data Collection Ethics

All data collection scripts implement the following best practices:
1. Appropriate delays between requests to avoid server overload
2. Proper user agent headers to identify the scraper
3. Comprehensive error handling and logging
4. Respect for website robots.txt files
5. Data is collected for research purposes only

## Data Storage

All collected data is stored in the following structure:
```
RawData/
└── Matches/
    ├── FBRef/
    ├── Football-data/
    ├── MatchURLs/
    └── todor/
```

## Requirements

The project requires Python 3.10 or higher and the following packages:
- beautifulsoup4
- pandas
- requests
- numpy

## Usage

Each script can be run independently to collect data from its respective source. The scripts will automatically handle rate limiting and data storage.
