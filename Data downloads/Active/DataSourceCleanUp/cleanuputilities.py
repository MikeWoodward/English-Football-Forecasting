#!/usr/bin/env python3
"""
Module for utility functions and classes for data validation and processing.

This module provides functions to validate data consistency and a class to
manage season-level data from multiple sources. It includes functionality for:
- Managing and analyzing season-level football data
- Validating club consistency across matches
- Checking season and league tier consistency
- Verifying club and match counts against reference data
"""

import logging
import pandas as pd
import os


def transform_club_names(*,
                        df: pd.DataFrame,
                        source_name: str,
                        target_name: str,
                        logger: logging.Logger) -> pd.DataFrame:
    """Normalize club names using a reference mapping.

    Args:
        df: DataFrame containing attendance data with club names to normalize
        source_name: Name of the source column containing club names
        target_name: Name of the target column for normalized club names

    Returns:
        DataFrame with normalized club names
    """
    logger.info(f"Transforming {source_name} to {target_name}...")

    # Load club name normalization mapping from CSV
    club_normalization_name = os.path.join(
        os.path.dirname(__file__),
        "club_name_normalization.csv"
    )
    try:
        club_normalization = pd.read_csv(club_normalization_name)
        # Strip whitespace from club names
        for column in club_normalization.columns:
            club_normalization[column] = club_normalization[column].str.strip()
    except FileNotFoundError:
        logger.error(f"File not found: {club_normalization_name}")
        return df

    # Check that all the club_names in source_name are in the club_name column, Stop if any are not. 
    unmatched_club = df[
        ~df[source_name].isin(club_normalization["club_name"])
    ][source_name].unique()
    if len(unmatched_club) > 0:
        logger.error(f"Found {len(unmatched_club)} unmatched clubs:")
        for club in sorted(unmatched_club):
            logger.error(f"  - {club}")

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