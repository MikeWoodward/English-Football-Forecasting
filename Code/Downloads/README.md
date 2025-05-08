# Football Data Collection Scripts

This repository contains Python scripts for collecting and processing football (soccer) data from various sources. Below is a comprehensive overview of the data sources and their usage.

## Data Sources

### 1. FBRef.com
**Used by:** `FBRef.py`
- **Purpose:** Scrapes match schedules, scores, and additional metadata
- **Data Collected:**
  - Match dates
  - Teams (home and away)
  - Scores
  - Attendance
  - Match report URLs
- **Server-friendly Practices:**
  - Implements random delays between requests
  - Uses proper user agent headers
  - Respects rate limits
  - Includes error handling and logging

### 2. football-data.co.uk
**Used by:** `FootballData.py`
- **Purpose:** Downloads historical match data
- **Data Collected:**
  - Match results
  - League standings
  - Historical data from 1993-2024
- **Server-friendly Practices:**
  - Implements 60-120 second random delays between requests
  - Uses proper user agent headers
  - Processes one league at a time
- **League Coverage:**
  - Premier League (E0)
  - Championship (E1)
  - League One (E2)
  - League Two (E3)
  - Conference/National League (EC)

### 3. Transfermarkt
**Used by:** `TransferValue.py`
- **Purpose:** Scrapes team market values and squad information
- **Data Collected:**
  - Club names
  - Squad sizes
  - Foreign player counts
  - Mean age
  - Total market values
- **Server-friendly Practices:**
  - 2-4 second random delays between requests
  - Proper user agent headers
  - Respects robots.txt
  - Error handling and logging
- **League Coverage:**
  - Premier League (Tier 1)
  - Championship (Tier 2)
  - League One (Tier 3)
  - League Two (Tier 4)

### 4. engsoccerdata (GitHub Repository)
**Used by:** `match_attendance5.py`
- **Purpose:** Downloads historical English football match data
- **Data Collected:**
  - Match results
  - League information
  - Historical data
- **Files Used:**
  - england.csv
  - england_nonleague.csv
- **Server-friendly Practices:**
  - Uses GitHub's raw content API
  - Implements timeout for requests
  - Error handling and logging

## Output Locations

All processed data is saved in the following directory structure:
```
../../RawData/Matches/
├── EngSoccerData/
│   └── engsoccerdata.csv
├── Football-data/
│   └── {tier_level}_{year}-{year+1}.csv
└── TransferValues/
    └── transfer_values_tier{tier}_{season}.csv
```

## General Best Practices

All scripts implement:
- Proper error handling
- Logging functionality
- Data validation
- Clean data processing
- Respectful web scraping practices
- Documentation and type hints

## Requirements

- Python >= 3.10
- pandas
- requests
- beautifulsoup4
- numpy
