# Data Sources Documentation

This document provides information about the data sources used in this project and what data is extracted from each source.

## TransferValue.py

### Source: [Transfermarkt](https://www.transfermarkt.com)
- **Data Extracted**: 
  - Team market values for Premier League clubs
  - Current season (2023/24) market valuations
  - Data includes:
    - Team names
    - Total market value per team
    - Season information

### Storage:
- Data is saved in: `RawData/Matches/TransferValues/transfer_values_{season}.csv`

## FBRef.py

### Source: [FBRef.com](https://fbref.com)
- **Data Extracted**:
  - Match schedules and results for English football leagues
  - Leagues covered:
    - Premier League (Tier 1)
    - Championship (Tier 2)
    - League One (Tier 3)
    - League Two (Tier 4)
  - Data includes:
    - Match dates
    - Home and away teams
    - Scores
    - Attendance figures
    - Match report URLs
    - League tier information

### Storage:
- Data is saved in: `RawData/Matches/FBRef/{league_tier}_{season_range}.csv`

## FootballData.py

### Source: [Football-Data.co.uk](https://www.football-data.co.uk)
- **Data Extracted**:
  - Historical match data for English football leagues
  - Leagues covered:
    - Premier League (E0 - Tier 1)
    - Championship (E1 - Tier 2)
    - League One (E2 - Tier 3)
    - League Two (E3 - Tier 4)
    - Conference/National League (EC - Tier 5)
  - Historical coverage: 1993-2024
  - Data includes:
    - Match results
    - Detailed statistics (specific fields vary by league and season)

### Storage:
- Data is saved in: `RawData/Matches/Football-data/{tier_level}_{year}-{year+1}.csv`

## Data Collection Ethics

All data collection scripts implement polite scraping practices:
- Random delays between requests (60-120 seconds)
- Proper user agent headers
- Error handling and rate limiting
- Respect for website terms of service

## Data Updates

- Transfer market values are updated for the current season
- Match data is collected historically and can be updated for current seasons
- Each script includes error handling and logging for failed requests 