# EPL Match Attendance Scraper

This Python script scrapes English Premier League match attendance data from web pages. It processes match URLs and extracts information including:

- Match date and time
- Home team name
- Away team name
- Match scores
- Attendance figures

## Features

- Polite web scraping with delays between requests
- Checkpoint saving every 100 matches
- Comprehensive error handling
- Progress tracking
- CSV output format

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

1. Place your match URLs in a text file at `../../RawData/Matches/MatchURLs/match_urls.txt`
2. Run the script:
```bash
python match_attendance4.py
```
3. Output will be saved to `../../CleansedData/Normalization/attendance2.csv`

## Output Format

The script generates CSV files with the following columns:
- match_date: Date of the match
- match_time: Time of the match
- home_team_name: Name of the home team
- away_team_name: Name of the away team
- match_home_score: Home team's score
- match_away_score: Away team's score
- attendance: Match attendance figure

## Error Handling

- Handles missing tables, rows, and data gracefully
- Provides detailed error messages with line numbers
- Continues processing even if some matches fail

## Checkpoints

Checkpoint files are saved every 100 matches as:
`attendance2_checkpoint_[N].csv` where N is the number of matches processed. 