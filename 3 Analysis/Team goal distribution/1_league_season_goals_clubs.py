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
    `3 Analysis/Team goal distribution/1_league_season_goals_clubs.py`
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


def merge_matches(
    match_df: pd.DataFrame,
    league_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge match and league data.
    """
    return pd.merge(
        left=match_df,
        right=league_df,
        on="league_id",
    )


def filter_club_matches(
    merged_df: pd.DataFrame,
    club_name: str,
    season: str,
    league_tier: int,
    club_type: str,
) -> pd.DataFrame:
    """
    Filter merged data for a specific club, season, and league tier.

    Parameters
    ----------
    merged_df:
        Merged DataFrame containing match and league data.
    club_name:
        Name of the club to filter for.
    season:
        Season to filter for.
    league_tier:
        League tier to filter for.
    club_type:
        Either 'home' or 'away' to filter by home_club or away_club.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    filtered = merged_df[
        (merged_df["season"] == season)
        & (merged_df["league_tier"] == league_tier)
    ]

    if club_type == "home":
        return filtered[filtered["home_club"] == club_name]
    elif club_type == "away":
        return filtered[filtered["away_club"] == club_name]
    else:
        raise ValueError(
            f"club_type must be 'home' or 'away', got {club_type}"
        )


def combine_goal_distributions(
    home_distribution_counts: pd.Series,
    away_distribution_counts: pd.Series,
) -> pd.Series:
    """
    Combine home and away goal distributions by summing frequencies.

    Parameters
    ----------
    home_distribution_counts:
        Series with home goal values as index and frequencies as values.
    away_distribution_counts:
        Series with away goal values as index and frequencies as values.

    Returns
    -------
    pd.Series
        Combined distribution with goal values as index and summed
        frequencies as values.
    """
    # Convert to dictionaries for easier merging
    home_dict = home_distribution_counts.to_dict()
    away_dict = away_distribution_counts.to_dict()

    # Combine dictionaries, summing frequencies for same goal values
    combined_dict: dict[int, int] = {}
    for goal_value, frequency in home_dict.items():
        combined_dict[int(goal_value)] = int(frequency)
    for goal_value, frequency in away_dict.items():
        goal_val_int = int(goal_value)
        if goal_val_int in combined_dict:
            combined_dict[goal_val_int] += int(frequency)
        else:
            combined_dict[goal_val_int] = int(frequency)

    # Convert back to Series, sorted by goal value
    combined_series = pd.Series(combined_dict).sort_index()
    return combined_series


def compute_goal_distribution(
    matches: pd.DataFrame,
    goals_column: str,
) -> tuple[pd.Series, float, np.ndarray, float, float]:
    """
    Compute observed goal relative frequency distribution and Poisson fit
    for aggregated matches for the given goals column.

    Parameters
    ----------
    matches:
        DataFrame containing match data.
    goals_column:
        Column name for goals (e.g., 'home_goals', 'away_goals', or
        'total_goals').

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
    distribution_counts = matches.groupby(
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


def compute_goal_distribution_from_counts(
    distribution_counts: pd.Series,
) -> tuple[pd.Series, float, np.ndarray, float, float]:
    """
    Compute observed goal relative frequency distribution and Poisson fit
    from a Series of goal counts.

    Parameters
    ----------
    distribution_counts:
        Series with goal values as index and frequencies as values.

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
    goals_label: str,
    distribution: pd.Series,
    fitted_proportions: np.ndarray,
    chi2_stat: float,
    chi2_p_value: float,
    show_poisson: bool = True,
) -> figure:
    """
    Create a Bokeh figure showing observed goal relative frequency
    distribution and optionally Poisson fitted proportions.

    Parameters
    ----------
    goals_label:
        Label for the goals type (e.g., 'Total', 'Home', 'Away').
    distribution:
        Series with observed relative frequencies.
    fitted_proportions:
        Expected relative frequencies under Poisson model.
    chi2_stat:
        Chi-square goodness-of-fit statistic.
    chi2_p_value:
        p-value for the chi-square goodness-of-fit test.
    show_poisson:
        Whether to show the Poisson fit line.

    Returns
    -------
    figure
        Bokeh figure object ready to be displayed.
    """
    goals = distribution.index.to_numpy()

    title = (
        f"{goals_label} Goals\n"
        f"χ²={chi2_stat:.2f}, p={chi2_p_value:.3f}"
    )

    p = figure(
        title=title,
        x_axis_label=f"{goals_label} Goals",
        y_axis_label="Relative Frequency",
        width=400,
        height=300,
    )

    p.vbar(
        x=goals,
        top=distribution.values,
        width=0.5,
        legend_label="Observed",
    )
    if show_poisson:
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
        # Merge match and league data
        merged_df = merge_matches(
            match_df=df,
            league_df=league_df,
        )
        print(
            f"Merged {len(merged_df):,} rows from goals and league data."
        )

        # Add total_goals column
        merged_df = merged_df.copy()
        merged_df["total_goals"] = (
            merged_df["home_goals"] + merged_df["away_goals"]
        )

        # Get all unique clubs from both home_club and away_club
        home_clubs = set(
            club
            for club in merged_df["home_club"].unique()
            if isinstance(club, str) and pd.notna(club)
        )
        away_clubs = set(
            club
            for club in merged_df["away_club"].unique()
            if isinstance(club, str) and pd.notna(club)
        )
        all_clubs = sorted(home_clubs | away_clubs)

        # Get all unique combinations of season and league_tier
        unique_season_tier = merged_df[
            ["season", "league_tier"]
        ].drop_duplicates().sort_values(
            by=["season", "league_tier"]
        )

        print(
            f"Found {len(all_clubs)} unique clubs and "
            f"{len(unique_season_tier)} unique season/league_tier "
            f"combinations"
        )

        # Build results dataframe
        results_data: list[dict[str, str | int | float]] = []

        for _, st_row in unique_season_tier.iterrows():
            season = str(st_row["season"])
            league_tier = int(st_row["league_tier"])

            # Filter matches for this season/league_tier
            season_tier_matches = merged_df[
                (merged_df["season"] == season)
                & (merged_df["league_tier"] == league_tier)
            ]

            # Get clubs that have matches in this season/league_tier
            clubs_in_season_tier = sorted(
                set(
                    club
                    for club in (
                        list(season_tier_matches["home_club"].unique())
                        + list(season_tier_matches["away_club"].unique())
                    )
                    if isinstance(club, str) and pd.notna(club)
                )
            )

            for club_name in clubs_in_season_tier:
                # Get home matches for this club
                home_matches = filter_club_matches(
                    merged_df=merged_df,
                    club_name=club_name,
                    season=season,
                    league_tier=league_tier,
                    club_type="home",
                )

                # Get away matches for this club
                away_matches = filter_club_matches(
                    merged_df=merged_df,
                    club_name=club_name,
                    season=season,
                    league_tier=league_tier,
                    club_type="away",
                )

                # Skip if no matches
                if len(home_matches) == 0 and len(away_matches) == 0:
                    continue

                # Compute home goals distribution
                if len(home_matches) > 0:
                    home_distribution_counts = (
                        home_matches.groupby("home_goals")
                        .size()
                        .sort_index()
                    )
                    (
                        _,
                        _,
                        _,
                        home_chi2,
                        home_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=home_distribution_counts,
                    )
                else:
                    home_chi2 = float("nan")
                    home_p = float("nan")
                    home_distribution_counts = pd.Series(
                        dtype=int,
                    )

                # Compute away goals distribution
                if len(away_matches) > 0:
                    away_distribution_counts = (
                        away_matches.groupby("away_goals")
                        .size()
                        .sort_index()
                    )
                    (
                        _,
                        _,
                        _,
                        away_chi2,
                        away_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=away_distribution_counts,
                    )
                else:
                    away_chi2 = float("nan")
                    away_p = float("nan")
                    away_distribution_counts = pd.Series(
                        dtype=int,
                    )

                # Combine home and away distributions for total goals
                if (
                    len(home_distribution_counts) > 0
                    or len(away_distribution_counts) > 0
                ):
                    total_distribution_counts = (
                        combine_goal_distributions(
                            home_distribution_counts=home_distribution_counts,
                            away_distribution_counts=away_distribution_counts,
                        )
                    )
                    (
                        _,
                        _,
                        _,
                        total_chi2,
                        total_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=total_distribution_counts,
                    )
                else:
                    total_chi2 = float("nan")
                    total_p = float("nan")

                results_data.append(
                    {
                        "league_tier": league_tier,
                        "season": season,
                        "club_name": club_name,
                        "total_goals_chi_squared": total_chi2,
                        "total_goals_p_value": total_p,
                        "away_goals_chi_squared": away_chi2,
                        "away_goals_p_value": away_p,
                        "home_goals_chi_squared": home_chi2,
                        "home_goals_p_value": home_p,
                    }
                )

        results_df = pd.DataFrame(results_data)
        print(
            f"\nProcessed {len(results_df)} club/season/league_tier "
            f"combinations"
        )

        # Sort by league_tier, season, and club_name
        results_df = results_df.sort_values(
            by=["league_tier", "season", "club_name"],
        ).reset_index(drop=True)

        # Save results dataframe to CSV
        csv_output_path = Path(__file__).with_suffix(".csv")
        results_df.to_csv(
            path_or_buf=csv_output_path,
            index=False,
        )
        print(
            f"Saved results to: {csv_output_path.name}"
        )

        # Find min and max total_goals_chi_squared (excluding NaN)
        valid_results = results_df[
            results_df["total_goals_chi_squared"].notna()
        ]
        if len(valid_results) == 0:
            print(
                "\nNo valid results with total_goals_chi_squared found."
            )
        else:
            min_idx = valid_results["total_goals_chi_squared"].idxmin()
            max_idx = valid_results["total_goals_chi_squared"].idxmax()

            min_row = results_df.loc[min_idx]
            max_row = results_df.loc[max_idx]

            print(
                f"\nLowest total_goals_chi_squared: "
                f"{min_row['club_name']}, {min_row['season']}, "
                f"league_tier={min_row['league_tier']}, "
                f"χ²={min_row['total_goals_chi_squared']:.2f}"
            )
            print(
                f"Highest total_goals_chi_squared: "
                f"{max_row['club_name']}, {max_row['season']}, "
                f"league_tier={max_row['league_tier']}, "
                f"χ²={max_row['total_goals_chi_squared']:.2f}"
            )

            # Generate charts for min and max cases
            charts: list[figure] = []

            for case_name, case_row in [
                ("Best", min_row),
                ("Worst", max_row),
            ]:
                club_name = str(case_row["club_name"])
                season = str(case_row["season"])
                league_tier = int(case_row["league_tier"])

                # Get home matches
                home_matches = filter_club_matches(
                    merged_df=merged_df,
                    club_name=club_name,
                    season=season,
                    league_tier=league_tier,
                    club_type="home",
                )

                # Get away matches
                away_matches = filter_club_matches(
                    merged_df=merged_df,
                    club_name=club_name,
                    season=season,
                    league_tier=league_tier,
                    club_type="away",
                )

                # Compute distributions
                if len(home_matches) > 0:
                    home_distribution_counts = (
                        home_matches.groupby("home_goals")
                        .size()
                        .sort_index()
                    )
                    (
                        home_distribution,
                        _,
                        home_fitted,
                        home_chi2,
                        home_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=home_distribution_counts,
                    )
                else:
                    home_distribution = pd.Series(dtype=float)
                    home_fitted = np.array([])
                    home_chi2 = float("nan")
                    home_p = float("nan")

                if len(away_matches) > 0:
                    away_distribution_counts = (
                        away_matches.groupby("away_goals")
                        .size()
                        .sort_index()
                    )
                    (
                        away_distribution,
                        _,
                        away_fitted,
                        away_chi2,
                        away_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=away_distribution_counts,
                    )
                else:
                    away_distribution = pd.Series(dtype=float)
                    away_fitted = np.array([])
                    away_chi2 = float("nan")
                    away_p = float("nan")

                # Combine for total
                if (
                    len(home_distribution_counts) > 0
                    or len(away_distribution_counts) > 0
                ):
                    total_distribution_counts = (
                        combine_goal_distributions(
                            home_distribution_counts=home_distribution_counts,
                            away_distribution_counts=away_distribution_counts,
                        )
                    )
                    (
                        total_distribution,
                        _,
                        total_fitted,
                        total_chi2,
                        total_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=total_distribution_counts,
                    )
                else:
                    total_distribution = pd.Series(dtype=float)
                    total_fitted = np.array([])
                    total_chi2 = float("nan")
                    total_p = float("nan")

                # Create plots
                if len(total_distribution) > 0:
                    total_plot = plot_goal_distribution(
                        goals_label="Total",
                        distribution=total_distribution,
                        fitted_proportions=total_fitted,
                        chi2_stat=total_chi2,
                        chi2_p_value=total_p,
                    )
                    total_plot.title = (
                        f"{case_name} Fit - Total Goals\n"
                        f"{club_name}, {season}, Tier {league_tier}\n"
                        f"χ²={total_chi2:.2f}, p={total_p:.3f}"
                    )
                else:
                    total_plot = None

                if len(home_distribution) > 0:
                    home_plot = plot_goal_distribution(
                        goals_label="Home",
                        distribution=home_distribution,
                        fitted_proportions=home_fitted,
                        chi2_stat=home_chi2,
                        chi2_p_value=home_p,
                    )
                    home_plot.title = (
                        f"{case_name} Fit - Home Goals\n"
                        f"{club_name}, {season}, Tier {league_tier}\n"
                        f"χ²={home_chi2:.2f}, p={home_p:.3f}"
                    )
                else:
                    home_plot = None

                if len(away_distribution) > 0:
                    away_plot = plot_goal_distribution(
                        goals_label="Away",
                        distribution=away_distribution,
                        fitted_proportions=away_fitted,
                        chi2_stat=away_chi2,
                        chi2_p_value=away_p,
                    )
                    away_plot.title = (
                        f"{case_name} Fit - Away Goals\n"
                        f"{club_name}, {season}, Tier {league_tier}\n"
                        f"χ²={away_chi2:.2f}, p={away_p:.3f}"
                    )
                else:
                    away_plot = None

                # Add plots to row (only if they exist)
                plot_list = [
                    p
                    for p in [total_plot, home_plot, away_plot]
                    if p is not None
                ]
                if plot_list:
                    charts.append(row(*plot_list))

            # Add Liverpool FC 2023-2024 charts
            liverpool_club_name = "Liverpool FC"
            liverpool_season = "2024-2025"
            
            # Find Liverpool FC's league_tier for 2023-2024
            liverpool_row = results_df[
                (results_df["club_name"] == liverpool_club_name)
                & (results_df["season"] == liverpool_season)
            ]
            
            if len(liverpool_row) > 0:
                liverpool_league_tier = int(liverpool_row.iloc[0]["league_tier"])
                
                # Get home matches
                liverpool_home_matches = filter_club_matches(
                    merged_df=merged_df,
                    club_name=liverpool_club_name,
                    season=liverpool_season,
                    league_tier=liverpool_league_tier,
                    club_type="home",
                )

                # Get away matches
                liverpool_away_matches = filter_club_matches(
                    merged_df=merged_df,
                    club_name=liverpool_club_name,
                    season=liverpool_season,
                    league_tier=liverpool_league_tier,
                    club_type="away",
                )

                # Compute distributions
                if len(liverpool_home_matches) > 0:
                    liverpool_home_distribution_counts = (
                        liverpool_home_matches.groupby("home_goals")
                        .size()
                        .sort_index()
                    )
                    (
                        liverpool_home_distribution,
                        _,
                        liverpool_home_fitted,
                        liverpool_home_chi2,
                        liverpool_home_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=liverpool_home_distribution_counts,
                    )
                else:
                    liverpool_home_distribution_counts = pd.Series(
                        dtype=int,
                    )
                    liverpool_home_distribution = pd.Series(dtype=float)
                    liverpool_home_fitted = np.array([])
                    liverpool_home_chi2 = float("nan")
                    liverpool_home_p = float("nan")

                if len(liverpool_away_matches) > 0:
                    liverpool_away_distribution_counts = (
                        liverpool_away_matches.groupby("away_goals")
                        .size()
                        .sort_index()
                    )
                    (
                        liverpool_away_distribution,
                        _,
                        liverpool_away_fitted,
                        liverpool_away_chi2,
                        liverpool_away_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=liverpool_away_distribution_counts,
                    )
                else:
                    liverpool_away_distribution_counts = pd.Series(
                        dtype=int,
                    )
                    liverpool_away_distribution = pd.Series(dtype=float)
                    liverpool_away_fitted = np.array([])
                    liverpool_away_chi2 = float("nan")
                    liverpool_away_p = float("nan")

                # Combine for total
                if (
                    len(liverpool_home_distribution_counts) > 0
                    or len(liverpool_away_distribution_counts) > 0
                ):
                    liverpool_total_distribution_counts = (
                        combine_goal_distributions(
                            home_distribution_counts=liverpool_home_distribution_counts,
                            away_distribution_counts=liverpool_away_distribution_counts,
                        )
                    )
                    (
                        liverpool_total_distribution,
                        _,
                        liverpool_total_fitted,
                        liverpool_total_chi2,
                        liverpool_total_p,
                    ) = compute_goal_distribution_from_counts(
                        distribution_counts=liverpool_total_distribution_counts,
                    )
                else:
                    liverpool_total_distribution = pd.Series(dtype=float)
                    liverpool_total_fitted = np.array([])
                    liverpool_total_chi2 = float("nan")
                    liverpool_total_p = float("nan")

                # Create plots
                if len(liverpool_total_distribution) > 0:
                    liverpool_total_plot = plot_goal_distribution(
                        goals_label="Total",
                        distribution=liverpool_total_distribution,
                        fitted_proportions=liverpool_total_fitted,
                        chi2_stat=liverpool_total_chi2,
                        chi2_p_value=liverpool_total_p,
                    )
                    liverpool_total_plot.title = (
                        f"Liverpool FC - Total Goals\n"
                        f"{liverpool_club_name}, {liverpool_season}, "
                        f"Tier {liverpool_league_tier}\n"
                        f"χ²={liverpool_total_chi2:.2f}, "
                        f"p={liverpool_total_p:.3f}"
                    )
                else:
                    liverpool_total_plot = None

                if len(liverpool_home_distribution) > 0:
                    liverpool_home_plot = plot_goal_distribution(
                        goals_label="Home",
                        distribution=liverpool_home_distribution,
                        fitted_proportions=liverpool_home_fitted,
                        chi2_stat=liverpool_home_chi2,
                        chi2_p_value=liverpool_home_p,
                    )
                    liverpool_home_plot.title = (
                        f"Liverpool FC - Home Goals\n"
                        f"{liverpool_club_name}, {liverpool_season}, "
                        f"Tier {liverpool_league_tier}\n"
                        f"χ²={liverpool_home_chi2:.2f}, "
                        f"p={liverpool_home_p:.3f}"
                    )
                else:
                    liverpool_home_plot = None

                if len(liverpool_away_distribution) > 0:
                    liverpool_away_plot = plot_goal_distribution(
                        goals_label="Away",
                        distribution=liverpool_away_distribution,
                        fitted_proportions=liverpool_away_fitted,
                        chi2_stat=liverpool_away_chi2,
                        chi2_p_value=liverpool_away_p,
                    )
                    liverpool_away_plot.title = (
                        f"Liverpool FC - Away Goals\n"
                        f"{liverpool_club_name}, {liverpool_season}, "
                        f"Tier {liverpool_league_tier}\n"
                        f"χ²={liverpool_away_chi2:.2f}, "
                        f"p={liverpool_away_p:.3f}"
                    )
                else:
                    liverpool_away_plot = None

                # Add plots to row (only if they exist)
                liverpool_plot_list = [
                    p
                    for p in [
                        liverpool_total_plot,
                        liverpool_home_plot,
                        liverpool_away_plot,
                    ]
                    if p is not None
                ]
                if liverpool_plot_list:
                    charts.append(row(*liverpool_plot_list))
                    print(
                        f"\nAdded charts for {liverpool_club_name} "
                        f"{liverpool_season}"
                    )
            else:
                print(
                    f"\nWarning: {liverpool_club_name} {liverpool_season} "
                    f"not found in results"
                )

            # Save plots to HTML file and display
            if charts:
                html_filename = Path(__file__).with_suffix(".html")
                output_file(
                    filename=str(html_filename),
                    title="Club Goal Distributions - Best/Worst Fit",
                )
                layout = column(*charts)
                save(layout)
                print(
                    f"\nSaved plots to: {html_filename.name}"
                )
                print(
                    "Displaying charts in browser..."
                )
                show(layout)
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

