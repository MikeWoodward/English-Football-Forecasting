# Websites Used in the Python Codebase

This document lists all the websites that are used in the Python files for data collection and web scraping. Each website serves a specific purpose in gathering football-related data.

## 1. Transfermarkt (transfermarkt.com)

**Purpose**: Collecting team and match data including market values, squad information, and attendance figures.

**Used in**:
- `TransferValue.py`: Scrapes team market values and squad information
- `MatchAttendance.py`: Collects match attendance data

**Specific URLs**:
- Premier League: `https://www.transfermarkt.com/premier-league/...`
- Championship: `https://www.transfermarkt.com/championship/...`
- League One: `https://www.transfermarkt.com/league-one/...`
- League Two: `https://www.transfermarkt.com/league-two/...`

## 2. Football-Data.co.uk (football-data.co.uk)

**Purpose**: Downloading historical football match data and statistics.

**Used in**: `FootballData.py`

**URL Format**: `https://www.football-data.co.uk/mmz4281/{season}/{league}.csv`

**Leagues covered**:
- E0 (Premier League)
- E1 (Championship)
- E2 (League One)
- E3 (League Two)
- EC (Conference/National League)

## 3. FBRef (fbref.com)

**Purpose**: Scraping detailed match data, schedules, and scores.

**Used in**: `FBRef.py`

**URL Format**: `https://fbref.com/en/comps/{league_index}/{season}/schedule/{season}-{league_name}-Scores-and-Fixtures`

## 4. World Football (worldfootball.net)

**Purpose**: Collecting historical match reports and data since 1892.

**Used in**: `match_attendance3.py`

**URL Format**: `https://www.worldfootball.net/all_matches/eng-{league}-{season}/`

**Leagues covered**:
- Premier League
- Championship
- League One
- League Two
- National League

## 5. Football Web Pages (footballwebpages.co.uk)

**Purpose**: Downloading football attendance data.

**Used in**: `match_attendance2.py`

## Common Features

All scripts implement ethical web scraping practices including:
- Random delays between requests (typically 2-4 seconds)
- Proper user agent headers
- Error handling and logging
- Respect for website rate limits 
