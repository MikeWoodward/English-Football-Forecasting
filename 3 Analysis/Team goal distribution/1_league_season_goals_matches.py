from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from bokeh.io import output_file, save, show
from bokeh.layouts import column, row
from bokeh.plotting import figure
from scipy import stats


DEFAULT_CSV_RELATIVE: Final[list[str]] = [
    "4 Database creation",
    "Football_Match",
    "Data",
    "football_match.csv",
]


def get_default_csv_path() -> Path:
    """
    Build the default CSV path relative to this repository.

    The current file lives in:
    `3 Analysis/Team goal distribution/1_league_season_goals_matches.py`
    The CSV lives in:
    `4 Database creation/Football match/Data/football_match.csv`
    """
    project_root = Path(__file__).resolve().parents[2]
    return project_root.joinpath(*DEFAULT_CSV_RELATIVE)


def load_league_season_goals(
    csv_path: str | Path,
) -> pd.DataFrame:
    """
    Load the league season goals data from the given CSV file.

    Parameters
    ----------
    csv_path:
        Path to `football_match.csv`.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the raw football match data.
    """
    csv_path_obj = (
        csv_path
        if isinstance(csv_path, Path)
        else Path(csv_path)
    )

    if not (resolved_path := csv_path_obj.expanduser().resolve()).is_file():
        raise FileNotFoundError(
            f"CSV file not found at: {resolved_path}"
        )

    return pd.read_csv(
        filepath_or_buffer=resolved_path,
        low_memory=False,
    )


def merge_and_filter_matches(
    match_df: pd.DataFrame,
    league_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge match and league data, then filter for league tier 1 and season
    2024-2025.
    """
    merged = pd.merge(
        left=match_df,
        right=league_df,
        on="league_id",
    )

    return merged[
        (merged["season"] == "2024-2025")
        & (merged["league_tier"] == 1)
    ]


def compute_goal_distribution(
    club_matches: pd.DataFrame,
    goals_column: str,
) -> tuple[pd.Series, float, np.ndarray, float, float]:
    """
    Compute observed goal relative frequency distribution and Poisson fit
    for a single club's matches for the given goals column.

    Returns
    -------
    distribution:
        Series indexed by goals value with observed relative frequencies
        (proportions).
    lambda_hat:
        Estimated Poisson mean.
    fitted_proportions:
        Expected relative frequencies for each goals value under the
        Poisson model, aligned to `distribution.index`.
    chi2_stat:
        Chi-square goodness-of-fit statistic.
    chi2_p_value:
        p-value for the chi-square goodness-of-fit test.
    """
    distribution_counts = club_matches.groupby(
        goals_column
    ).size().sort_index()

    total_matches = int(distribution_counts.values.sum())
    goals = distribution_counts.index.to_numpy()

    lambda_hat = (
        float((goals * distribution_counts.values).sum())
        / float(total_matches)
    )

    # Compute fitted counts
    fitted_counts = (
        stats.poisson.pmf(
            k=goals,
            mu=lambda_hat,
        )
        * total_matches
    )

    # Ensure expected counts sum matches observed (within tolerance)
    scale = distribution_counts.values.sum() / fitted_counts.sum()
    scaled_expected_counts = fitted_counts * scale

    # Convert to relative frequencies (proportions)
    distribution = distribution_counts / total_matches
    fitted_proportions = scaled_expected_counts / total_matches

    # Chi-square test uses absolute counts, not proportions
    chi2_stat, chi2_p_value = stats.chisquare(
        f_obs=distribution_counts.values,
        f_exp=scaled_expected_counts,
    )

    return distribution, lambda_hat, fitted_proportions, chi2_stat, chi2_p_value


def plot_goal_distribution(
    *,
    club_name: str,
    goals_label: str,
    distribution: pd.Series,
    fitted_proportions: np.ndarray,
    chi2_stat: float,
    chi2_p_value: float,
) -> figure:
    """
    Create a Bokeh figure showing observed goal relative frequency
    distribution and Poisson fitted proportions for a single club.

    Returns
    -------
    figure
        Bokeh figure object ready to be displayed.
    """
    goals = distribution.index.to_numpy()

    p = figure(
        title=(
            f"{goals_label} Goals - {club_name} "
            f"(χ²={chi2_stat:.2f}, p={chi2_p_value:.3f})"
        ),
        x_axis_label=f"{goals_label} Goals",
        y_axis_label="Relative Frequency",
        width=600,
        height=300,
    )

    p.vbar(
        x=goals,
        top=distribution.values,
        width=0.5,
        legend_label="Observed",
    )
    p.line(
        x=goals,
        y=fitted_proportions,
        line_width=2,
        line_color="red",
        legend_label="Poisson fit",
    )

    p.legend.location = "top_right"
    p.legend.click_policy = "hide"

    return p


if __name__ == "__main__":
    try:
        csv_path = get_default_csv_path()
        df = load_league_season_goals(
            csv_path=csv_path,
        )
        print(
            f"Loaded {len(df):,} rows from goals data."
        )
        # Read in league.csv from 4 Database creation/League/Data/league.csv
        league_csv_path = Path(__file__).resolve().parents[2].joinpath(
            "4 Database creation",
            "League",
            "Data",
            "league.csv",
        )
        league_df = pd.read_csv(
            filepath_or_buffer=league_csv_path,
            low_memory=False,
        )
        print(
            f"Loaded {len(league_df):,} rows from league data"
        )
        # Merge and filter for league tier 1 and season 2024-2025
        merged_df = merge_and_filter_matches(
            match_df=df,
            league_df=league_df,
        )
        print(
            f"Merged and filtered {len(merged_df):,} "
            f"rows from goals and league data."
        )
        # For each home club (alphabetical), compute and plot distributions
        home_clubs = sorted(
            club
            for club in merged_df["home_club"].unique()
            if isinstance(club, str)
        )

        plots: list[figure] = []
        for club_name in home_clubs:
            club_matches = merged_df[
                merged_df["home_club"] == club_name
            ]
            if club_matches.empty:
                continue

            (
                home_distribution,
                home_lambda,
                home_fitted,
                home_chi2,
                home_p,
            ) = compute_goal_distribution(
                club_matches=club_matches,
                goals_column="home_goals",
            )
            (
                away_distribution,
                away_lambda,
                away_fitted,
                away_chi2,
                away_p,
            ) = compute_goal_distribution(
                club_matches=club_matches,
                goals_column="away_goals",
            )

            print(
                f"{club_name}: {len(club_matches):,} home matches, "
                f"λ̂_home={home_lambda:.4f}, "
                f"λ̂_away={away_lambda:.4f}"
            )

            home_plot = plot_goal_distribution(
                club_name=club_name,
                goals_label="Home",
                distribution=home_distribution,
                fitted_proportions=home_fitted,
                chi2_stat=home_chi2,
                chi2_p_value=home_p,
            )
            away_plot = plot_goal_distribution(
                club_name=club_name,
                goals_label="Away",
                distribution=away_distribution,
                fitted_proportions=away_fitted,
                chi2_stat=away_chi2,
                chi2_p_value=away_p,
            )

            plots.append(
                row(
                    home_plot,
                    away_plot,
                )
            )

        # Save all club plots to HTML file with _matches suffix
        if plots:
            html_filename = Path(__file__).with_suffix(".html")
            output_file(
                filename=str(html_filename),
                title="League Season Goals - Matches",
            )
            layout = column(
                *plots,
            )
            save(layout)
            show(layout)
            print(
                f"Saved plots to: {html_filename.name}"
            )
    except Exception as exc:
        import sys
        import traceback

        _, _, tb = sys.exc_info()
        if tb and (tb_last := traceback.extract_tb(tb)[-1]):
            line_no = tb_last.lineno
        else:
            line_no = "unknown"

        print(
            f"Error on line {line_no}: "
            f"{type(exc).__name__}: {exc}"
        )
        raise


