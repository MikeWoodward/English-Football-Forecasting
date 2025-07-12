"""
Analysis utilities module for EPL predictor.

This module contains utility functions for data analysis and processing.
"""
import logging
import os
from typing import List, Optional

import pandas as pd


class SeasonData:
    """
    A class to manage and analyze season-level data from multiple sources.

    This class provides methods to access and analyze season-specific
    information such as available seasons, club counts, and match counts for
    different league tiers. It serves as a central repository for season-level
    metadata and validation.
    """

    def __init__(self, logger: logging.Logger) -> None:
        """
        Initialize the SeasonData class by reading and preparing the data.

        The method reads league size and match data from a CSV file containing
        information about league sizes and match counts across different
        seasons and league tiers.

        Raises:
            FileNotFoundError: If the required input file is not found.
            pd.errors.EmptyDataError: If the input file is empty.
            ValueError: If the data cannot be properly loaded or is empty.
        """
        self.logger = logger
        self.logger.info("Initializing SeasonData")

        # Build the path to the league size and matches CSV file
        file_path = os.path.join(
            os.path.dirname(__file__),
            "league_size_matches.csv"
        )

        # Check if the file exists before attempting to read
        if not os.path.exists(file_path):
            error_msg = f"Required file not found: {file_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Attempt to read the CSV file with error handling
        try:
            self.football_data = pd.read_csv(file_path)
            self.logger.info(
                f"Successfully loaded football data: "
                f"{self.football_data.shape}"
            )
        except pd.errors.EmptyDataError:
            error_msg = f"File is empty: {file_path}"
            self.logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise

        # Ensure the loaded DataFrame is not empty
        if self.football_data.empty:
            error_msg = "Loaded football data is empty"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info("SeasonData initialized successfully")

    def get_seasons(self, *, league_tier: Optional[int] = None) -> List[int]:
        """
        Get all available seasons for a specific league tier or all seasons if
        no tier is specified.

        Args:
            league_tier (Optional[int]): The league tier to filter by (e.g., 1
                                       for Premier League). If None, returns
                                       seasons for all tiers.

        Returns:
            List[int]: List of seasons available for the specified league tier
                      or all seasons if no tier is specified.

        Raises:
            ValueError: If league_tier is provided but is not a positive
                       integer.
        """
        # Validate league tier if provided
        if league_tier is not None:
            if not isinstance(league_tier, int) or league_tier < 1:
                raise ValueError("League tier must be a positive integer")
            # Filter for seasons in the specified league tier
            seasons = sorted(
                self.football_data[
                    self.football_data['league_tier'] == league_tier
                ]['season'].unique().tolist()
            )
            self.logger.info(
                f"Found {len(seasons)} seasons for league tier "
                f"{league_tier}"
            )
        else:
            # Get all unique seasons across all tiers
            seasons = sorted(self.football_data['season'].unique().tolist())
            self.logger.info(
                f"Found {len(seasons)} seasons across all league tiers"
            )
        return seasons

    def get_club_count(self, *, season: int, league_tier: int) -> int:
        """
        Get the number of clubs in a specific season and league tier.

        Args:
            season (int): The season to analyze.
            league_tier (int): The league tier to analyze.

        Returns:
            int: Number of unique clubs in the specified season and league tier.

        Raises:
            ValueError: If league_tier is invalid.
        """
        # Get expected club count from the reference data
        if not isinstance(league_tier, int):
            raise ValueError("League tier must be an integer")

        mask = (
            (self.football_data['season'] == season) &
            (self.football_data['league_tier'] == league_tier)
        )
        if not mask.any():
            error_msg = (
                f"No data for season {season}, league tier {league_tier}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        club_count = int(self.football_data.loc[mask, 'clubs'].iloc[0])
        self.logger.info(
            "Found %s clubs in season %s, "
            "league t"
            "ier %s",
            club_count,
            season,
            league_tier
        )
        return club_count

    def get_match_count(self, *, season: int, league_tier: int) -> int:
        """
        Get the number of matches in a specific season and league tier.

        Args:
            season: The season to analyze.
            league_tier: The league tier to analyze.

        Returns:
            int: Number of matches in the specified season and league tier.

        Raises:
            ValueError: If league_tier is invalid.
        """
        if not isinstance(league_tier, int):
            raise ValueError("League tier must be an integer")

        mask = (
            (self.football_data['season'] == season) &
            (self.football_data['league_tier'] == league_tier)
        )
        if not mask.any():
            error_msg = (
                f"No data for season {season}, league tier {league_tier}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        match_count = int(self.football_data.loc[mask, 'matches'].iloc[0])
        self.logger.info(
            f"Found {match_count} matches in season {season}, "
            f"league tier {league_tier}"
        )
        return match_count

    def get_league_tiers(self) -> List[int]:
        """
        Get all available league tiers in the dataset.

        Returns:
            List[int]: Sorted list of unique league tiers present in the data.

        Raises:
            ValueError: If no league tiers are found in the data.
        """
        # Get unique league tiers and sort them
        league_tiers = sorted(
            self.football_data['league_tier'].unique().tolist()
        )

        # Ensure at least one league tier is present
        if not league_tiers:
            error_msg = "No league tiers found in the data"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info(
            f"Found {len(league_tiers)} league tiers: {league_tiers}"
        )
        return league_tiers

    def check_leagues_seasons(self, *, matches: pd.DataFrame) -> bool:
        """
        Check that league seasons in matches dataframe match reference data.

        Args:
            matches (pd.DataFrame): DataFrame containing match data.

        Returns:
            bool: True if league seasons match reference data.

        Raises:
            ValueError: If league seasons validation fails.
        """
        matches_summary = (
            matches[['season', 'league_tier']]
            .drop_duplicates()
            .sort_values(by=['season', 'league_tier'])
            .reset_index(drop=True)
        )
        matches_summary['league_tier'] = matches_summary['league_tier'].astype(
            int
        )
        football_data_summary = (
            self.football_data[['season', 'league_tier']]
            .drop_duplicates()
            .sort_values(by=['season', 'league_tier'])
            .reset_index(drop=True)
        )
        football_data_summary['league_tier'] = (
            football_data_summary['league_tier'].astype(int)
        )
        if not matches_summary.equals(football_data_summary):
            error_msg = "League seasons validation failed"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            return True
        
    def check_leagues_seasons_clubs(self, *, matches: pd.DataFrame) -> bool:
        """
        Check that league seasons in matches dataframe match reference data.

        Args:
            matches (pd.DataFrame): DataFrame containing match data.

        Returns:
            bool: True if league seasons match reference data.

        Raises:
            ValueError: If league seasons validation fails.
        """
        matches_summary = (
            matches[['season', 'league_tier', 'home_club']]
            .groupby(['season', 'league_tier'])
            .nunique()
            .reset_index()
            .rename({'home_club': 'clubs'}, axis=1)
            .sort_values(by=['season', 'league_tier'])
        )
        matches_summary['league_tier'] = matches_summary['league_tier'].astype(
            int
        )
        
        football_data_summary = (
            self.football_data[['season', 'league_tier', 'clubs']]
            .sort_values(by=['season', 'league_tier'])
        )
        football_data_summary['league_tier'] = football_data_summary['league_tier'].astype(
            int
        )

        differences = football_data_summary.merge(
            matches_summary,
            on=["season", "league_tier"],
            suffixes=["_expected", "_actual"],
            how="outer"
        )
        differences = differences[differences['clubs_expected'] != differences['clubs_actual']]
        if not differences.empty:
            error_msg = "League seasons clubs validation failed"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            return True

    def check_leagues_seasons_matches(self, *, matches: pd.DataFrame) -> bool:
        """
        Check that league seasons in matches dataframe match reference data.

        Args:
            matches (pd.DataFrame): DataFrame containing match data.

        Returns:
            bool: True if league seasons match reference data.

        Raises:
            ValueError: If league seasons validation fails.
        """
        matches_summary = (
            matches[['season', 'league_tier', 'home_club']]
            .groupby(['season', 'league_tier'])
            .count()
            .reset_index()
            .rename({'home_club': 'matches'}, axis=1)
            .sort_values(by=['season', 'league_tier'])
        )
        matches_summary['league_tier'] = matches_summary['league_tier'].astype(
            int
        )
        
        football_data_summary = (
            self.football_data[['season', 'league_tier', 'matches']]
            .sort_values(by=['season', 'league_tier'])
        )
        football_data_summary['league_tier'] = football_data_summary['league_tier'].astype(
            int
        )

        differences = football_data_summary.merge(
            matches_summary,
            on=["season", "league_tier"],
            suffixes=["_expected", "_actual"],
            how="outer"
        )
        differences = differences[differences['matches_expected'] != differences['matches_actual']]
        if not differences.empty:
            error_msg = "League seasons matches validation failed"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        else:
            return True


def check_clubs_1(*,
                  matches: pd.DataFrame,
                  error_stop: bool = True,
                  logger: logging.Logger) -> bool:
    """
    Check that clubs are consistent in the matches dataframe.

    This function performs three key validations:
    1. Checks for null values in club columns
    2. Verifies no team plays against itself
    3. Ensures clubs appear in only one league tier per season

    Args:
        matches (pd.DataFrame): DataFrame containing match data.
        error_stop (bool): If True, raises an exception on error. If False,
                          returns False on error.
        logger (logging.Logger): Logger instance for logging messages.

    Returns:
        bool: True if clubs are consistent, False otherwise.

    Raises:
        ValueError: If error_stop is True and clubs are inconsistent.
    """
    logger.info("Checking club consistency in matches dataframe - part 1")

    # Check for null values in club columns
    if (matches['home_club'].isnull().any() or
            matches['away_club'].isnull().any()):
        error_msg = "Found null values in home_club or away_club columns"
        logger.error(error_msg)
        if error_stop:
            raise ValueError(error_msg)
        return False

    # Check for self-matches (team playing against itself)
    self_matches = matches[matches['home_club'] == matches['away_club']]
    if not self_matches.empty:
        error_msg = "Found self-matches"
        logger.error(error_msg)
        if error_stop:
            raise ValueError(error_msg)
        return False

    # Check club tier consistency per season
    club_tiers = matches.groupby(
        ['home_club', 'season']
    )['league_tier'].nunique()
    if (club_tiers > 1).any():
        error_msg = (
            "Found clubs that appear in multiple league tiers per season "
            f"clubs: {club_tiers[club_tiers > 1]}"
        )
        logger.error(error_msg)
        if error_stop:
            raise ValueError(error_msg)
        return False

    logger.info("Club consistency check passed")
    return True


def check_clubs_2(*,
                  matches: pd.DataFrame,
                  error_stop: bool = True,
                  logger: logging.Logger) -> bool:
    """
    Check that clubs appear both as home and away teams in the matches dataframe.

    This function verifies that each club appears both as a home team and an
    away team in each season and league tier combination.

    Args:
        matches (pd.DataFrame): DataFrame containing match data.
        error_stop (bool): If True, raises an exception on error. If False,
                          returns False on error.
        logger (logging.Logger): Logger instance for logging messages.

    Returns:
        bool: True if clubs appear both home and away, False otherwise.

    Raises:
        ValueError: If error_stop is True and clubs are inconsistent.
    """
    logger.info("Checking club consistency in matches dataframe - part 2")

    # Create separate dataframes for home and away teams
    away_only = (
        matches[['season', 'league_tier', 'away_club']]
        .rename(columns={'away_club': 'club'})
        .drop_duplicates()
    )
    home_only = (
        matches[['season', 'league_tier', 'home_club']]
        .rename(columns={'home_club': 'club'})
        .drop_duplicates()
    )

    # Combine home and away appearances, then group by club/season/tier
    one_leg = (
        pd.concat([away_only, home_only])
        .assign(club_name=lambda x: x['club'])
        .groupby(['season', 'league_tier', 'club_name'])
        .count()
        .reset_index()
        .rename(columns={'club': 'count'})
    )

    # Find clubs that only appear once (either only home or only away)
    one_leg = one_leg[
        one_leg['count'] != 2
    ]

    if one_leg.shape[0] > 0:
        error_msg_fmt = (
            "Found clubs that only appear as home or away "
            + "teams: %s"
        )
        error_msg = (
            "Found clubs that only appear as home or away teams: "
        )
        error_msg += str(one_leg.to_dict(orient='records'))
        logger.error(error_msg_fmt, str(one_leg.to_dict(orient='records')))
        if error_stop:
            raise ValueError(error_msg)
        return False

    logger.info("Club consistency check (part 2) passed")
    return True
