#!/usr/bin/env python3
"""
Module for utility functions and classes for data validation and processing.

This module provides functions to validate data consistency and a class to manage
season-level data from multiple sources. It includes functionality for:
- Managing and analyzing season-level football data
- Validating club consistency across matches
- Checking season and league tier consistency
- Verifying club and match counts against reference data
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SeasonData:
    """
    A class to manage and analyze season-level data from multiple sources.

    This class provides methods to access and analyze season-specific information
    such as available seasons, club counts, and match counts for different
    league tiers. It serves as a central repository for season-level metadata
    and validation.
    """

    def __init__(self) -> None:
        """
        Initialize the SeasonData class by reading and preparing the data.

        The method reads league size and match data from a CSV file containing
        information about league sizes and match counts across different seasons
        and league tiers.

        Raises:
            FileNotFoundError: If the required input file is not found.
            pd.errors.EmptyDataError: If the input file is empty.
            ValueError: If the data cannot be properly loaded or is empty.
        """
        logger.info("Initializing SeasonData")
        
        # Define the path to the league size and matches file
        file_path = Path(
            "../../CleansedData/Corrections and normalization/"
            "league_size_matches.csv"
        )
        
        # Verify file existence
        if not file_path.exists():
            error_msg = f"Required file not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Attempt to read the CSV file with error handling
        try:
            self.football_data = pd.read_csv(file_path)
            logger.info(
                f"Successfully loaded football data: "
                f"{self.football_data.shape}"
            )
        except pd.errors.EmptyDataError:
            error_msg = f"File is empty: {file_path}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise
        
        # Validate that data was loaded successfully
        if self.football_data.empty:
            error_msg = "Loaded football data is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("SeasonData initialized successfully")

    def get_seasons(self, *, league_tier: Optional[int] = None) -> List[int]:
        """
        Get all available seasons for a specific league tier or all seasons if no
        tier is specified.

        Args:
            league_tier (Optional[int]): The league tier to filter by (e.g., 1 for
                                       Premier League). If None, returns seasons
                                       for all tiers.

        Returns:
            List[int]: List of seasons available for the specified league tier or
                      all seasons if no tier is specified.

        Raises:
            ValueError: If league_tier is provided but is not a positive integer.
        """
        # Validate league tier if provided
        if league_tier is not None:
            if not isinstance(league_tier, int) or league_tier < 1:
                raise ValueError("League tier must be a positive integer")
            # Filter seasons for specific league tier
            seasons = sorted(
                self.football_data[
                    self.football_data['league_tier'] == league_tier
                ]['season'].unique().tolist()
            )
            logger.info(
                f"Found {len(seasons)} seasons for league tier {league_tier}"
            )
        else:
            # Get all unique seasons across all tiers
            seasons = sorted(self.football_data['season'].unique().tolist())
            logger.info(
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
            ValueError: If season or league_tier is invalid.
        """
        # Validate input parameters
        if not isinstance(season, int) or not isinstance(league_tier, int):
            raise ValueError("Season and league tier must be integers")

        # Filter data for specific season and tier
        mask = (
            (self.football_data['season'] == season) &
            (self.football_data['league_tier'] == league_tier)
        )
        # Count unique home teams (each team must play at home)
        club_count = len(
            self.football_data[mask]['home_team'].unique()
        )
        logger.info(
            f"Found {club_count} clubs in season {season}, "
            f"league tier {league_tier}"
        )
        return club_count

    def get_match_count(self, *, season: int, league_tier: int) -> int:
        """
        Get the number of matches in a specific season and league tier.

        Args:
            season (int): The season to analyze.
            league_tier (int): The league tier to analyze.

        Returns:
            int: Number of matches in the specified season and league tier.

        Raises:
            ValueError: If season or league_tier is invalid.
        """
        # Validate input parameters
        if not isinstance(season, int) or not isinstance(league_tier, int):
            raise ValueError("Season and league tier must be integers")

        # Filter data for specific season and tier
        mask = (
            (self.football_data['season'] == season) &
            (self.football_data['league_tier'] == league_tier)
        )
        # Count total matches
        match_count = len(self.football_data[mask])
        logger.info(
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
        
        # Validate that we found at least one league tier
        if not league_tiers:
            error_msg = "No league tiers found in the data"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(
            f"Found {len(league_tiers)} league tiers: {league_tiers}"
        )
        return league_tiers


def check_clubs_1(*, matches: pd.DataFrame, error_stop: bool = True) -> bool:
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

def check_clubs_2(*, matches: pd.DataFrame, error_stop: bool = True) -> bool:
    """
    Check that clubs appear both as home and away teams in the matches dataframe.

    This function verifies that each club appears both as a home team and an away
    team in each season and league tier combination.

    Args:
        matches (pd.DataFrame): DataFrame containing match data.
        error_stop (bool): If True, raises an exception on error. If False,
                          returns False on error.

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

    # Combine and analyze home/away appearances
    one_leg = (
        pd.concat([away_only, home_only])
        .assign(club_name=lambda x: x['club'])
        .groupby(['season', 'league_tier', 'club_name'])
        .count()
        .reset_index()
        .rename(columns={'club': 'count'})
    )

    # Find clubs that only appear once (either only home or only away)
    one_leg = one_leg[one_leg['count'] != 2]
    
    if one_leg.shape[0] > 0:
        error_msg = (
            "Found clubs that only appear as home or away teams: "
            f"{one_leg.to_dict(orient='records')}"
        )
        logger.error(error_msg)
        if error_stop:
            raise ValueError(error_msg)
        return False

def check_seasons(matches: pd.DataFrame, *, error_stop: bool = True) -> bool:
    """
    Check that seasons and league_tiers are consistent in the matches dataframe.

    This function validates:
    1. No null values in season or league_tier columns
    2. Each season has all expected league tiers

    Args:
        matches (pd.DataFrame): DataFrame containing match data.
        error_stop (bool): If True, raises an exception on error. If False,
                          returns False on error.

    Returns:
        bool: True if seasons and league_tiers are consistent, False otherwise.

    Raises:
        ValueError: If error_stop is True and seasons/league_tiers are inconsistent.
    """
    logger.info("Checking season and league tier consistency")
    
    # Check for null values
    null_seasons = matches['season'].isnull().sum()
    null_tiers = matches['league_tier'].isnull().sum()
    
    if null_seasons > 0 or null_tiers > 0:
        error_msg = (
            f"Found null values in season ({null_seasons}) or "
            f"league_tier ({null_tiers}) columns"
        )
        logger.error(error_msg)
        if error_stop:
            raise ValueError(error_msg)
        return False
    
    # Check league tier consistency across seasons
    season_tiers = matches.groupby('season')['league_tier'].nunique()
    expected_tiers = matches['league_tier'].nunique()
    
    inconsistent_seasons = season_tiers[season_tiers != expected_tiers]
    if not inconsistent_seasons.empty:
        error_msg = (
            f"Found seasons with inconsistent league tiers: "
            f"{inconsistent_seasons.to_dict()}"
        )
        logger.error(error_msg)
        if error_stop:
            raise ValueError(error_msg)
        return False
    
    logger.info("Season and league tier consistency check passed")
    return True


def check_club_counts(*,
    matches: pd.DataFrame,
    season_data: SeasonData,
    error_stop: bool = True
) -> bool:
    """
    Check that club counts are consistent with SeasonData.

    This function verifies that the number of clubs in each season and league
    tier combination matches the expected counts from the SeasonData reference.

    Args:
        matches (pd.DataFrame): DataFrame containing match data.
        season_data (SeasonData): SeasonData instance for validation.
        error_stop (bool): If True, raises an exception on error. If False,
                          returns False on error.

    Returns:
        bool: True if club counts are consistent, False otherwise.

    Raises:
        ValueError: If error_stop is True and club counts are inconsistent.
    """
    logger.info("Checking club counts against SeasonData")
    
    # Get unique seasons and league tiers from matches
    seasons = matches['season'].unique()
    league_tiers = matches['league_tier'].unique()
    
    # Validate club counts for each season/tier combination
    for season in seasons:
        for tier in league_tiers:
            # Get expected count from reference data
            expected_count = season_data.get_club_count(
                season=season,
                league_tier=tier
            )
            
            # Calculate actual count from matches
            mask = (
                (matches['season'] == season) &
                (matches['league_tier'] == tier)
            )
            actual_count = len(
                matches[mask]['home_club'].unique()
            )
            
            # Compare counts
            if actual_count != expected_count:
                error_msg = (
                    f"Club count mismatch for season {season}, "
                    f"league tier {tier}: expected {expected_count}, "
                    f"got {actual_count}"
                )
                logger.error(error_msg)
                if error_stop:
                    raise ValueError(error_msg)
                return False
    
    logger.info("Club count consistency check passed")
    return True


def check_match_counts(*,
    matches: pd.DataFrame,
    season_data: SeasonData,
    error_stop: bool = True
) -> bool:
    """
    Check that match counts are consistent with SeasonData.

    This function verifies that the number of matches in each season and league
    tier combination matches the expected counts from the SeasonData reference.

    Args:
        matches (pd.DataFrame): DataFrame containing match data.
        season_data (SeasonData): SeasonData instance for validation.
        error_stop (bool): If True, raises an exception on error. If False,
                          returns False on error.

    Returns:
        bool: True if match counts are consistent, False otherwise.

    Raises:
        ValueError: If error_stop is True and match counts are inconsistent.
    """
    logger.info("Checking match counts against SeasonData")
    
    # Get unique seasons and league tiers from matches
    seasons = matches['season'].unique()
    league_tiers = matches['league_tier'].unique()
    
    # Validate match counts for each season/tier combination
    for season in seasons:
        for tier in league_tiers:
            # Get expected count from reference data
            expected_count = season_data.get_match_count(
                season=season,
                league_tier=tier
            )
            
            # Calculate actual count from matches
            mask = (
                (matches['season'] == season) &
                (matches['league_tier'] == tier)
            )
            actual_count = len(matches[mask])
            
            # Compare counts
            if actual_count != expected_count:
                error_msg = (
                    f"Match count mismatch for season {season}, "
                    f"league tier {tier}: expected {expected_count}, "
                    f"got {actual_count}"
                )
                logger.error(error_msg)
                if error_stop:
                    raise ValueError(error_msg)
                return False
    
    logger.info("Match count consistency check passed")
    return True 

def transform_club_names(*, 
                         df: pd.DataFrame,
                         source_name: str, 
                         target_name: str) -> pd.DataFrame:
    """Normalize club names using a reference mapping.
    
    Args:
        df: DataFrame containing attendance data with club names to normalize
        
    Returns:
        DataFrame with normalized club names
    """
    logger.info(f"Transforming {source_name} to {target_name}...")

    # Load club name normalization mapping from CSV
    club_normalization_path = Path(
        "../../CleansedData/Corrections and normalization/"
        "club_name_normalization.csv"
    )
    try:    
        club_normalization = pd.read_csv(club_normalization_path)
    except FileNotFoundError:
        logger.error(f"File not found: {club_normalization_path}")
        return df
    
    # Check that all the club_names in source_name are in the club_name column
    unmatched_club = df[~df[source_name].isin(club_normalization["club_name"])][source_name].unique()
    if len(unmatched_club) > 0:
        logger.warning(f"Found {len(unmatched_club)} unmatched clubs:")
        for club in sorted(unmatched_club):
            logger.warning(f"  - {club}")
    
    # Normalize source_name club names using merge operation
    df = df.merge(
        club_normalization,
        left_on=source_name,
        right_on='club_name',
        how='left'
    )
    df = df.drop(columns=[source_name, 'club_name'])
    df = df.rename(columns={'club_name_normalized': target_name})
    
    return df