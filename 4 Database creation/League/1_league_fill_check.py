#!/usr/bin/env python3
"""Checks that league.csv contains data on all leagues from the ENFA dataset.

This module validates that all league names from the ENFA dataset exist in the
league.csv file. The league.csv file will be loaded into the database as the
league table, so it must contain complete league information for all leagues
referenced in the ENFA data.
"""

import pandas as pd
from pathlib import Path
import logging


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Define project root as the current working directory
        project_root = Path.cwd()
        # Read in the league.csv file from the League/Data folder
        league_path = (
            project_root /
            "League" /
            "Data" /
            "league_baseline.csv"
        )
        logger.info(f"Reading league data from: {league_path}")
        league = pd.read_csv(league_path, low_memory=False)
        logger.info(f"Loaded {len(league)} league records")

        # Read in the matches.csv file from the 2 Data preparation/Data folder
        matches_path = (
            project_root.parent /
            "2 Data preparation" /
            "Data" /
            "matches.csv"
        )
        logger.info(f"Reading matches data from: {matches_path}")
        matches = pd.read_csv(matches_path, low_memory=False)
        logger.info(f"Loaded {len(matches)} match records")

        # Merge to get missing start and end dates for each league
        start_end = (
            matches.groupby(['league_tier', 'season'])['match_date']
            .agg(['min', 'max'])
            .reset_index()
            .rename(columns={
                'league_tier': 'tier',
                'min': 'season_start',
                'max': 'season_end'
            })
        )
        league = league[['season', 'name', 'tier', 'notes']].merge(
            start_end, on=['season', 'tier'], how='left'
        )

        # Read in league_size_matches.csv file from the League/Data folder
        league_size_matches_path = (
            project_root.parent /
            "2 Data preparation" /
            "Testing Data" /
            "league_size_matches.csv"
        )
        logger.info(f"Reading league size matches data from: {league_size_matches_path}")
        league_size_matches = pd.read_csv(league_size_matches_path, low_memory=False).rename(columns={
            'leaguetier': 'tier',
            'matches': 'league_size_matches',
            'clubs': 'league_size_clubs'
        }).rename(columns={
            'clubs': 'league_clubs',
            'matches': 'league_matches',
            'league_tier': 'tier'
        })

        # Merge the league_size_matches dataframe with the league dataframe
        league = league.merge(league_size_matches, on=['season', 'tier'], how='left')

        # Sanity checks before we write to disk

        # 1. For each tier, report on any non-contiguous seasons
        league['start_year'] = (
            league['season'].str.split('-').str[0].astype(int)
        )

        league = league.sort_values(by=['tier', 'start_year'])
        league['start_year_diff'] = league['start_year'].diff()

        print('Non-contiguous seasons.')
        print('-----------------------')
        print('Action is to make sure these are the correct seasons.')
        non_contiguous = league[league['start_year_diff'] != 1]
        print(non_contiguous[['season', 'name', 'tier', 'notes']]
              .sort_values(by=['season', 'tier']))

        # Write to disk
        league = league.rename(columns={
            'name': 'league_name',
            'tier': 'league_tier',
            'notes': 'league_notes'
        })

        # Create a unique id for each row
        league['league_id'] = (
            league['league_tier'] * 10000 +
            league['season'].str.split('-').str[0].astype(int)
        )

        league = league[[
            'league_id', 'season', 'league_tier', 'league_name',
            'season_start', 'season_end', 
            'league_size_matches', 'league_size_clubs',
            'league_notes'
        ]].sort_values(by=['season', 'league_tier'])

        logger.info(f"Writing league data to: {league_path}")
        # Save to file name league.csv in the League/Data folder
        league_path = (
            project_root /
            "League" /
            "Data" /
            "league.csv"
        )
        league.to_csv(league_path, index=False)

    except FileNotFoundError as e:
        logger.error(
            f"File not found at line {e.__traceback__.tb_lineno}: {e}"
        )
        logger.error(f"Error occurred in: {e.filename}")
    except Exception as e:
        logger.error(
            f"Unexpected error at line {e.__traceback__.tb_lineno}: {e}"
        )
        logger.error(
            f"Error occurred in: "
            f"{e.__traceback__.tb_frame.f_code.co_filename}"
        )
