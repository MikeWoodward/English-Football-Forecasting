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
    `3 Analysis/Team goal distribution/1_league_season_goals.py`
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


def filter_matches(
    merged_df: pd.DataFrame,
    season: str,
    league_tier: int,
) -> pd.DataFrame:
    """
    Filter merged data for a specific season and league tier.
    """
    return merged_df[
        (merged_df["season"] == season)
        & (merged_df["league_tier"] == league_tier)
    ]


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

        # Get all unique combinations of season and league_tier
        unique_combinations = merged_df[
            ["season", "league_tier"]
        ].drop_duplicates().sort_values(
            by=["season", "league_tier"]
        )

        print(
            f"Found {len(unique_combinations)} unique season/league_tier "
            f"combinations"
        )

        # Build results dataframe
        results_data: list[dict[str, str | int | float]] = []

        for _, combo_row in unique_combinations.iterrows():
            season = str(combo_row["season"])
            league_tier = int(combo_row["league_tier"])

            filtered_df = filter_matches(
                merged_df=merged_df,
                season=season,
                league_tier=league_tier,
            )

            if len(filtered_df) == 0:
                continue

            # Compute distributions for aggregated data
            (
                total_distribution,
                _,
                _,
                total_chi2,
                total_p,
            ) = compute_goal_distribution(
                matches=filtered_df,
                goals_column="total_goals",
            )
            (
                home_distribution,
                _,
                _,
                home_chi2,
                home_p,
            ) = compute_goal_distribution(
                matches=filtered_df,
                goals_column="home_goals",
            )
            (
                away_distribution,
                _,
                _,
                away_chi2,
                away_p,
            ) = compute_goal_distribution(
                matches=filtered_df,
                goals_column="away_goals",
            )

            results_data.append(
                {
                    "season": season,
                    "league_tier": league_tier,
                    "total_goals_chi_squared": total_chi2,
                    "total_goals_chie_probability": total_p,
                    "away_goals_chi_squared": away_chi2,
                    "away_goals_chie_probability": away_p,
                    "home_goals_chi_squared": home_chi2,
                    "home_goals_chie_probability": home_p,
                }
            )

        results_df = pd.DataFrame(results_data)
        print(
            f"\nProcessed {len(results_df)} season/league_tier combinations"
        )

        # Sort by league_tier and season
        results_df = results_df.sort_values(
            by=["league_tier", "season"],
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

        # Find min and max total_goals_chi_squared
        min_idx = results_df["total_goals_chi_squared"].idxmin()
        max_idx = results_df["total_goals_chi_squared"].idxmax()

        min_row = results_df.loc[min_idx]
        max_row = results_df.loc[max_idx]

        print(
            f"\nLowest total_goals_chi_squared: "
            f"{min_row['season']}, league_tier={min_row['league_tier']}, "
            f"χ²={min_row['total_goals_chi_squared']:.2f}"
        )
        print(
            f"Highest total_goals_chi_squared: "
            f"{max_row['season']}, league_tier={max_row['league_tier']}, "
            f"χ²={max_row['total_goals_chi_squared']:.2f}"
        )

        # Generate charts for min and max cases
        charts: list[figure] = []

        for case_name, case_row, case_type in [
            ("Lowest", min_row, "lowest"),
            ("Highest", max_row, "highest"),
        ]:
            case_df = filter_matches(
                merged_df=merged_df,
                season=str(case_row["season"]),
                league_tier=int(case_row["league_tier"]),
            )

            (
                total_distribution,
                _,
                total_fitted,
                total_chi2,
                total_p,
            ) = compute_goal_distribution(
                matches=case_df,
                goals_column="total_goals",
            )
            (
                home_distribution,
                _,
                home_fitted,
                home_chi2,
                home_p,
            ) = compute_goal_distribution(
                matches=case_df,
                goals_column="home_goals",
            )
            (
                away_distribution,
                _,
                away_fitted,
                away_chi2,
                away_p,
            ) = compute_goal_distribution(
                matches=case_df,
                goals_column="away_goals",
            )

            total_plot = plot_goal_distribution(
                goals_label="Total",
                distribution=total_distribution,
                fitted_proportions=total_fitted,
                chi2_stat=total_chi2,
                chi2_p_value=total_p,
            )
            total_plot.title = (
                f"{case_name} χ² - Total Goals\n"
                f"{case_row['season']}, Tier {case_row['league_tier']}\n"
                f"χ²={total_chi2:.2f}, p={total_p:.3f}"
            )

            home_plot = plot_goal_distribution(
                goals_label="Home",
                distribution=home_distribution,
                fitted_proportions=home_fitted,
                chi2_stat=home_chi2,
                chi2_p_value=home_p,
            )
            home_plot.title = (
                f"{case_name} χ² - Home Goals\n"
                f"{case_row['season']}, Tier {case_row['league_tier']}\n"
                f"χ²={home_chi2:.2f}, p={home_p:.3f}"
            )

            away_plot = plot_goal_distribution(
                goals_label="Away",
                distribution=away_distribution,
                fitted_proportions=away_fitted,
                chi2_stat=away_chi2,
                chi2_p_value=away_p,
            )
            away_plot.title = (
                f"{case_name} χ² - Away Goals\n"
                f"{case_row['season']}, Tier {case_row['league_tier']}\n"
                f"χ²={away_chi2:.2f}, p={away_p:.3f}"
            )

            charts.append(
                row(
                    total_plot,
                    home_plot,
                    away_plot,
                )
            )

        # Save plots to HTML file
        html_filename = Path(__file__).with_suffix(".html")
        output_file(
            filename=str(html_filename),
            title="League Season Goals - Min/Max Chi-Squared",
        )
        layout = column(*charts)
        save(layout)
        show(layout)
        print(
            f"\nSaved plots to: {html_filename.name}"
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


