#!/usr/bin/env python3
"""
Home Field Advantage Analysis Module

This module provides functions to analyze football match data including
home field advantage for winning games and scoring extra goals
"""


import logging
import pandas as pd
from bokeh.plotting import figure, show, column
from bokeh.palettes import Category10
from bokeh.embed import file_html, components
from bokeh.resources import CDN
from typing import Dict
from bokeh.models import BoxAnnotation, Span
import numpy as np
import os
# Configure logging for tracking execution progress and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, file_path: str) -> pd.DataFrame:
    """
    Read CSV data file and return a Pandas dataframe.

    Args:
        file_path: Path to the CSV file containing match data.

    Returns:
        pd.DataFrame: DataFrame containing the match data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the CSV file is empty.
        pd.errors.ParserError: If the CSV file cannot be parsed.
    """
    try:
        logger.info(
            f"Reading data from {file_path}"
        )
        data = pd.read_csv(file_path, low_memory=False)
        logger.info(
            f"Successfully loaded {len(data)} rows of data"
        )
        return data
    except FileNotFoundError:
        # Handle case where file doesn't exist
        logger.error(
            f"File not found: {file_path}"
        )
        raise
    except pd.errors.EmptyDataError:
        # Handle case where CSV file is empty
        logger.error(
            f"CSV file is empty: {file_path}"
        )
        raise
    except pd.errors.ParserError as e:
        # Handle CSV parsing errors
        logger.error(
            f"Error parsing CSV file {file_path}: {e}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"Unexpected error reading file {file_path}: {e}"
        )
        raise


def _create_color_palette(*, leagues: list) -> Dict[str, str]:
    """
    Create a color palette mapping for league tiers.

    Args:
        leagues: List of league tier names.

    Returns:
        Dictionary mapping league names to colors.
    """
    palette = Category10[max(3, min(10, len(leagues)))]
    return {
        league: palette[i % len(palette)]
        for i, league in enumerate(leagues)
    }


def _add_historical_annotations(*, plot: figure) -> None:
    """
    Add historical annotations to the plot.

    Args:
        plot: Bokeh figure object to annotate.
    """
    # WWII period (1939-1945)
    wwii_band = BoxAnnotation(
        left=1939, right=1945,
        fill_color='lightcoral', fill_alpha=0.3
    )
    plot.add_layout(wwii_band)

    # WWI period (1914-1918)
    wwi_band = BoxAnnotation(
        left=1914, right=1918,
        fill_color='lightcoral', fill_alpha=0.3
    )
    plot.add_layout(wwi_band)


def _configure_legend(*, plot: figure) -> None:
    """
    Configure the legend for the plot.

    Args:
        plot: Bokeh figure object to configure.
    """
    plot.legend.title = 'League\nTier'
    plot.legend.click_policy = "hide"
    plot.legend.location = "right"
    plot.legend.orientation = "vertical"
    plot.legend.spacing = 10
    plot.legend.margin = 20
    plot.legend.padding = 10
    plot.legend.border_line_color = "black"
    plot.legend.border_line_width = 1
    plot.legend.background_fill_color = "white"
    plot.legend.background_fill_alpha = 0.8
    # Place legend outside the plot
    plot.add_layout(plot.legend[0], 'right')


def plot_win_fraction(*, match_data: pd.DataFrame, std: bool = True) -> figure:
    """
    Create and display a plot of home win fractions vs season for each league.

    Args:
        match_data: DataFrame containing match data with columns:
                   'season', 'league_tier', 'home_goals', 'away_goals'
        std: Whether to include standard error bands.

    Returns:
        figure: Bokeh figure object containing the plot.

    Raises:
        ValueError: If match_data is missing required columns.
        KeyError: If expected keys are not found in match_data.
    """
    try:
        logger.info("Creating home win fraction visualization")

        # Copy to prevent mutating the original data
        home_win_fraction = match_data.copy()

        home_win_fraction['season_start'] = (
            home_win_fraction['season']
            .str.split('-')
            .str[0]
            .astype(int)
        )

        # Home wins (home team scores more goals)
        home_win_fraction['home_wins'] = (
            home_win_fraction['home_goals'] > home_win_fraction['away_goals']
        )

        # All matches (excluding draws for win fraction calculation)
        home_win_fraction['all_matches'] = (
            home_win_fraction['home_goals'] != home_win_fraction['away_goals']
        )

        # Calculate home win fraction by season and league tier
        home_win_fraction = home_win_fraction.groupby(
            ['season_start', 'league_tier']
        ).agg({
            'home_wins': 'sum',
            'all_matches': 'sum',
        }).reset_index()

        # Calculate home win fraction
        home_win_fraction['home_win_fraction'] = (
            home_win_fraction['home_wins'] / home_win_fraction['all_matches']
        )

        # Calculate standard error of proportion using binomial distribution
        # SE = sqrt(p * (1-p) / n) where p is proportion and n is sample size
        home_win_fraction['home_win_fraction_std'] = np.sqrt(
            home_win_fraction['home_win_fraction'] *
            (1 - home_win_fraction['home_win_fraction']) /
            home_win_fraction['all_matches']
        )

        # Get unique league tiers and sort them for consistent ordering
        leagues = sorted(home_win_fraction['league_tier'].unique())
        color_map = _create_color_palette(leagues=leagues)

        # Set title based on whether confidence intervals are shown
        title = (
            "Home Win Fraction vs Season for All League Tiers - "
            "with std - interactive chart"
            if std else "Home Win Fraction vs Season for All League Tiers - "
            "no std - interactive chart"
        )

        # Create the main figure with appropriate dimensions and labels
        p = figure(
            title=title,
            x_axis_label="Season",
            y_axis_label="Home Win Fraction",
            width=600,
            height=400
        )

        # Add historical annotations
        _add_historical_annotations(plot=p)

        # Plot data for each league tier
        for league in leagues:
            # Filter data for current league tier
            league_data = home_win_fraction[
                home_win_fraction['league_tier'] == league
            ]

            # Plot the main trend line connecting win fractions over time
            p.line(
                league_data['season_start'],
                league_data['home_win_fraction'],
                legend_label=f"{league}",
                line_width=2,
                color=color_map[league]
            )

            # Add confidence interval bands if requested
            if std:
                p.varea(
                    x=league_data['season_start'],
                    y1=league_data['home_win_fraction'] -
                    league_data['home_win_fraction_std'],
                    y2=league_data['home_win_fraction'] +
                    league_data['home_win_fraction_std'],
                    legend_label=f"{league}",
                    fill_color=color_map[league],
                    fill_alpha=0.3
                )

            # Add scatter points to show individual data points
            p.scatter(
                league_data['season_start'],
                league_data['home_win_fraction'],
                legend_label=f"{league}",
                size=8,
                color=color_map[league]
            )

        # Configure legend
        _configure_legend(plot=p)

        logger.info("Home win fraction visualization completed")
        return p

    except KeyError as e:
        # Handle missing required keys in the data
        logger.error(
            f"Missing required key in match_data: {e}"
        )
        raise
    except ValueError as e:
        # Handle invalid data for plotting
        logger.error(
            f"Invalid data for plotting: {e}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during plotting
        logger.error(
            f"Unexpected error in plotting: {e}"
        )
        raise


def plot_goal_advantage(*, match_data: pd.DataFrame, std: bool = True) -> figure:
    """
    Create and display a plot of home goal advantage vs season for each league.

    Args:
        match_data: DataFrame containing match data with columns:
                   'season', 'league_tier', 'home_goals', 'away_goals'
        std: Whether to include standard error bands.

    Returns:
        figure: Bokeh figure object containing the plot.

    Raises:
        ValueError: If match_data is missing required columns.
        KeyError: If expected keys are not found in match_data.
    """
    try:
        logger.info("Creating home goal advantage visualization")

        # Copy to prevent mutating the original data
        g = match_data.copy()

        g['season_start'] = (
            g['season']
            .str.split('-')
            .str[0]
            .astype(int)
        )

        # Calculate home goal advantage (positive = home team advantage)
        g['home_goal_advantage'] = (
            g['home_goals'] - g['away_goals']
        )

        # Calculate mean goal advantage by season and league tier
        g = g.groupby(
            ['season_start', 'league_tier']
        ).agg(
            home_goal_advantage_mean= pd.NamedAgg(
                column='home_goal_advantage',
                aggfunc='mean'
            ),
            matches_played_count= pd.NamedAgg(
                column='home_club',
                aggfunc='count'
            ),
        ).reset_index()

        # Calculate standard error of the mean
        # SE = std / sqrt(n) where std is sample standard deviation
        # For now, we'll use a simplified approach since we don't have
        # individual match std
        g['std'] = (
            g['home_goal_advantage_mean']
            / np.sqrt(g['matches_played_count'])
        )

        # Get unique league tiers and sort them for consistent ordering
        leagues = sorted(g['league_tier'].unique())
        color_map = _create_color_palette(leagues=leagues)

        # Set title
        title = (
            "Home Goal Advantage vs Season for All League Tiers - "
            "interactive chart"
        )

        # Create the main figure with appropriate dimensions and labels
        p = figure(
            title=title,
            x_axis_label="Season",
            y_axis_label="Home Goal Advantage",
            width=600,
            height=400
        )

        # Add historical annotations
        _add_historical_annotations(plot=p)

        # Plot data for each league tier
        for league in leagues:
            # Filter data for current league tier
            league_data = g[
                g['league_tier'] == league
            ]

            # Plot the main trend line connecting goal advantages over time
            p.line(
                league_data['season_start'],
                league_data['home_goal_advantage_mean'],
                legend_label=f"{league}",
                line_width=2,
                color=color_map[league]
            )

            # Add confidence interval bands if requested
            if std:
                p.varea(
                    x=league_data['season_start'],
                    y1=league_data['home_goal_advantage_mean'] - league_data['std'],
                    y2=league_data['home_goal_advantage_mean'] + league_data['std'],
                    legend_label=f"{league}",
                    fill_color=color_map[league],
                    fill_alpha=0.3
                )

            # Add scatter points to show individual data points
            p.scatter(
                league_data['season_start'],
                league_data['home_goal_advantage_mean'],
                legend_label=f"{league}",
                size=8,
                color=color_map[league]
            )

        # Configure legend
        _configure_legend(plot=p)

        logger.info("Home goal advantage visualization completed")
        return p

    except KeyError as e:
        # Handle missing required keys in the data
        logger.error(
            f"Missing required key in match_data: {e}"
        )
        raise
    except ValueError as e:
        # Handle invalid data for plotting
        logger.error(
            f"Invalid data for plotting: {e}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during plotting
        logger.error(
            f"Unexpected error in plotting: {e}"
        )
        raise


if __name__ == "__main__":
    # Main execution block - demonstrates how to use the analysis functions
    try:
        # Read the match data from CSV file
        match_data = read_data(
            file_path=os.path.join("Data", "merged_match_data.csv")
        )

        # Create plots with and without standard error bands
        win_fraction_plot_std = plot_win_fraction(
            match_data=match_data, std=True
        )
        win_fraction_plot_no_std = plot_win_fraction(
            match_data=match_data, std=False
        )

        home_advantage_plot = plot_goal_advantage(
            match_data=match_data, std=True
        )
        home_advantage_plot_no_std = plot_goal_advantage(
            match_data=match_data, std=False
        )

        # Chart layout as columns
        layout = column(
            win_fraction_plot_std,
            win_fraction_plot_no_std,
            home_advantage_plot,
            home_advantage_plot_no_std,
        )

        # Save HTML to file with proper error handling
        try:
            html = file_html(layout, CDN, "Home Advantage Analysis")
            with open("Plots/plot.html", "w") as f:
                f.write(html)
            logger.info("Successfully saved plot.html")
        except Exception as e:
            logger.error(f"Error saving plot.html: {e}")
            raise

        # Save individual plot components
        plots = [
            win_fraction_plot_std,
            win_fraction_plot_no_std,
            home_advantage_plot,
            home_advantage_plot_no_std
        ]

        for index, plot in enumerate(plots):
            try:
                script, div = components(plot)
                with open(f"Plots/script_{index}.txt", "w") as f:
                    f.write(script)
                with open(f"Plots/div_{index}.txt", "w") as f:
                    f.write(div)
                logger.info(
                    f"Successfully saved plot components for index {index}"
                )
            except Exception as e:
                logger.error(
                    f"Error saving plot components for index {index}: {e}"
                )
                raise

        # Display the interactive plot
        show(layout)

    except Exception as e:
        # Log any errors that occur during main execution
        logger.error(
            f"Error in main execution: {e}"
        )
        raise 
