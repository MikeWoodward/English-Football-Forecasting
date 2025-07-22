# Import required libraries for data processing, visualization, and logging
import logging
import sys
import pandas as pd
import matplotlib.pyplot as plt
import traceback


# Configure logging for debugging and monitoring
# Sets up logging to display timestamp, log level, and message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, file_path: str) -> pd.DataFrame:
    """
    Read data from CSV file.

    Args:
        file_path: Path to the CSV file to read.

    Returns:
        DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If the file cannot be parsed as CSV.
    """
    try:
        # Log the file reading operation for debugging purposes
        logger.info(f"Reading data from {file_path}")
        # Read CSV file into pandas DataFrame
        data = pd.read_csv(file_path)
        # Log successful data loading with dimensions for verification
        logger.info(
            f"Successfully loaded {len(data)} rows and "
            f"{len(data.columns)} columns"
        )
        return data
    except FileNotFoundError:
        # Handle missing file error with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"File not found: {file_path} at line {line_number}"
        )
        raise
    except pd.errors.EmptyDataError:
        # Handle empty file error with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"File is empty: {file_path} at line {line_number}"
        )
        raise
    except pd.errors.ParserError:
        # Handle CSV parsing error with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error parsing CSV file: {file_path} at line {line_number}"
        )
        raise


def prepare_data(*, match_data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and modify the match data for 3D visualization.

    Args:
        match_data: Raw match data DataFrame to be processed.

    Returns:
        Modified DataFrame ready for 3D visualization.
    """
    try:
        # Log the start of data preparation process
        logger.info("Preparing data for 3D visualization")

        # Create a copy to avoid modifying the original data
        # (defensive programming)
        prepared_data = match_data.copy()

        # Combine home and away goals into a single score string for grouping
        # Format: "home_goals-away_goals" (e.g., "2-1", "0-0")
        prepared_data['score'] = (
            prepared_data['home_goals'].astype(str) + "-" +
            prepared_data['away_goals'].astype(str)
        )

        # Group by season, league tier, and score to count occurrences
        # This creates frequency data for each unique score combination
        score_frequencies = (
            prepared_data.groupby(["season", 'league_tier', 'score'])
            .agg(score_count=pd.NamedAgg(column='score', aggfunc='count'))
            .reset_index()
        )

        # Calculate total matches per season and league tier for normalization
        # This is needed to convert raw counts to proportions/frequencies
        normalize = score_frequencies.groupby(['season', 'league_tier']).agg(
            total_score_count=pd.NamedAgg(
                column='score_count', aggfunc='sum'
            )
        )
        # Merge total counts back to calculate frequencies
        # This joins the total counts with individual score counts
        score_frequencies = score_frequencies.merge(
            normalize, on=['season', 'league_tier'], how='left'
        )
        # Calculate frequency as proportion of total matches
        # This normalizes the data so frequencies sum to 1 for each season/tier
        score_frequencies['frequency'] = (
            score_frequencies['score_count'] /
            score_frequencies['total_score_count']
        )
        # Extract home and away goals from score string for plotting
        # Split the "home-away" string and convert to integers for axis labels
        score_frequencies['home_goals'] = (
            score_frequencies['score'].str.split('-').str[0].astype(int)
        )
        score_frequencies['away_goals'] = (
            score_frequencies['score'].str.split('-').str[1].astype(int)
        )
        # Remove temporary columns used for calculations to clean up the data
        score_frequencies = score_frequencies.drop(
            columns=['score_count', 'total_score_count']
        )

        # Log successful completion with final data shape
        logger.info(
            f"Data preparation complete. Shape: {prepared_data.shape}"
        )
        return score_frequencies

    except Exception as e:
        # Handle any unexpected errors during data preparation with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error preparing data: {str(e)} at line {line_number}"
        )
        raise


def create_heatmap(*, data: pd.DataFrame) -> None:
    """
    Create heatmap visualizations for football match data.

    Args:
        data: Prepared DataFrame containing match data with frequencies.

    Raises:
        ValueError: If data is empty or missing required columns.
        KeyError: If required settings keys are missing.
        RuntimeError: If matplotlib plotting fails.
    """
    try:
        # Validate input data
        if data.empty:
            raise ValueError("Input data is empty")

        required_columns = [
            'season', 'league_tier', 'home_goals', 'away_goals', 'frequency'
        ]
        missing_columns = [
            col for col in required_columns if col not in data.columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Define the settings for the heatmap
        # Each setting contains parameters for a specific season/league
        # combination
        settings = [
            {
                'season': '1888-1889',
                'league_tier': 1,
                'position': 121,  # Subplot position (1 row, 2 columns, pos 1)
                'max_home_goals': 0,  # Will be calculated dynamically
                'max_away_goals': 0,   # Will be calculated dynamically
                'max_frequency': 0,  # Will be calculated dynamically
                'heatmap_data': None
            },
            {
                'season': '2024-2025',
                'league_tier': 1,
                'position': 122,  # Subplot position (1 row, 2 columns, pos 2)
                'max_home_goals': 0,  # Will be calculated dynamically
                'max_away_goals': 0,   # Will be calculated dynamically
                'max_frequency': 0, # Will be calculated dynamically
                'heatmap_data': None
            }
        ]

        # Extract unique seasons and league tiers from settings for data
        # filtering
        seasons = [setting['season'] for setting in settings]
        league_tiers = [setting['league_tier'] for setting in settings]

        # Filter the data to only include the seasons and league tiers we want
        # to plot
        df = data[
            (data['season'].isin(seasons)) &
            (data['league_tier'].isin(league_tiers))
        ]

        # Check if filtered data is empty
        if df.empty:
            raise ValueError(
                f"No data found for seasons {seasons} and league tiers "
                f"{league_tiers}"
            )

        # Calculate the maximum goals across all filtered data for consistent
        # axis scaling
        max_home_goals = df['home_goals'].max()
        max_away_goals = df['away_goals'].max()
        max_frequency = df['frequency'].max()

        # Create dummy frame for missing home_goals and away_goals
        dummy = pd.DataFrame(
            [[0] for a in range(0, max_home_goals + 1)
             for b in range(0, max_away_goals + 1)],
            columns=['frequency'],
            index=pd.MultiIndex.from_tuples(
                [(a, b) for a in range(0, max_home_goals + 1)
                 for b in range(0, max_away_goals + 1)],
                names=['home_goals', 'away_goals']
            )
        )

        # Validate calculated values
        if max_home_goals < 0 or max_away_goals < 0:
            raise ValueError("Negative goal values found in data")

        # Process each setting to prepare heatmap data
        for setting in settings:
            try:
                # Validate setting has required keys
                required_keys = ['season', 'league_tier', 'position']
                missing_keys = [
                    key for key in required_keys if key not in setting
                ]
                if missing_keys:
                    raise KeyError(
                        f"Missing required keys in setting: {missing_keys}"
                    )

                # Set the maximum goals for consistent scaling across all plots
                setting['max_home_goals'] = max_home_goals
                setting['max_away_goals'] = max_away_goals
                setting['max_frequency'] = max_frequency

                # Filter data for this specific season and league tier, copy
                # because we're going to do some manipulation on the data
                df_selection = df[
                    (df['season'] == setting['season']) &
                    (df['league_tier'] == setting['league_tier'])
                ][['home_goals', 'away_goals', 'frequency']].copy()

                # Check if selection is empty
                if df_selection.empty:
                    logger.warning(
                        f"No data found for season {setting['season']} "
                        f"league tier {setting['league_tier']}"
                    )
                    continue

                # Fill in missing home_goals and away_goals by re-indexing and
                # adding zeros from the dummy frame. Do not remove na values.
                df_selection = df_selection.set_index(
                    ['home_goals', 'away_goals']
                )
                df_selection = df_selection + dummy
                df_selection = df_selection.reset_index()

                # Create pivot table and convert to numpy array for heatmap
                # plotting
                # This transforms the data into a 2D matrix where
                # rows=home_goals,
                # cols=away_goals
                pivot_data = df_selection.pivot(
                    index='away_goals',
                    columns='home_goals',
                    values='frequency'
                )

                # Check if pivot operation was successful
                if pivot_data.empty:
                    logger.warning(
                        f"Pivot operation produced empty data for "
                        f"{setting['season']} {setting['league_tier']}"
                    )
                    continue

                setting['heatmap_data'] = pivot_data.to_numpy()

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                line_number = traceback.extract_tb(exc_traceback)[-1].lineno
                logger.error(
                    f"Error processing setting "
                    f"{setting.get('season', 'unknown')}: "
                    f"{str(e)} at line {line_number}"
                )
                continue

        # Set up the figure with subplots
        try:
            # Create the main figure for all subplots with specified size
            fig = plt.figure(figsize=(9, 4))
            # Add a main title for the entire figure
            fig.suptitle('Scores heatmaps', fontsize=16, fontweight='bold')
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_number = traceback.extract_tb(exc_traceback)[-1].lineno
            raise RuntimeError(
                f"Failed to create matplotlib figure: {str(e)} at line "
                f"{line_number}"
            )

        # Create subplots for each setting
        for setting in settings:
            try:
                # Skip if no heatmap data available
                if setting['heatmap_data'] is None:
                    logger.warning(
                        f"Skipping plot for {setting['season']} - "
                        f"no data available"
                    )
                    continue

                # Create 3D subplot with specified position
                ax = fig.add_subplot(setting['position'])

                # Set the x and y limits to the maximum goals for consistent
                # scaling
                ax.set_xlim(-0.5, max_home_goals + 0.5)
                ax.set_ylim(-0.5, max_away_goals + 0.5)

                # Create the heatmap visualization using imshow
                im1 = ax.imshow(
                    setting['heatmap_data'],
                    cmap='viridis',
                    aspect='auto',
                    vmin=0,
                    vmax=setting['max_frequency']
                )
                # Set subplot title and axis labels
                ax.set_title(
                    f'Season: {setting["season"]} League Tier: '
                    f'{setting["league_tier"]}'
                )
                ax.set_xlabel('Home Goals')
                ax.set_ylabel('Away Goals')
                # Add colorbar to show the mapping between colors and values

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                line_number = traceback.extract_tb(exc_traceback)[-1].lineno
                logger.error(
                    f"Error creating subplot for "
                    f"{setting.get('season', 'unknown')}: "
                    f"{str(e)} at line {line_number}"
                )
                continue

        # Adjust layout to prevent overlap between subplots
        try:
            # Add colorbar to show the mapping between colors and values
            plt.colorbar(im1, ax=ax)
            plt.tight_layout()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_number = traceback.extract_tb(exc_traceback)[-1].lineno
            logger.warning(
                f"Failed to adjust layout: {str(e)} at line {line_number}"
            )

        # Display the plot
        try:
            plt.show()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            line_number = traceback.extract_tb(exc_traceback)[-1].lineno
            raise RuntimeError(
                f"Failed to display plot: {str(e)} at line {line_number}"
            )

    except ValueError as e:
        # Handle data validation errors
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Data validation error: {str(e)} at line {line_number}"
        )
        raise
    except KeyError as e:
        # Handle missing key errors
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Missing key error: {str(e)} at line {line_number}"
        )
        raise
    except RuntimeError as e:
        # Handle matplotlib runtime errors
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Runtime error: {str(e)} at line {line_number}"
        )
        raise
    except Exception as e:
        # Handle any other unexpected errors
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Unexpected error in create_heatmap: {str(e)} at line "
            f"{line_number}"
        )
        raise


if __name__ == "__main__":
    # Main execution block - only runs if script is executed directly
    logger.info("Starting 3D bar chart visualization")

    # Define the input data file path relative to the script location
    data_file = "Data/merged_match_data.csv"

    try:
        # Read the match data from CSV file using the read_data function
        match_data = read_data(file_path=data_file)

        # Prepare the data for visualization using the prepare_data function
        prepared_data = prepare_data(match_data=match_data)

        # Create and display the 3D bar charts using the create_heatmap
        # function
        create_heatmap(data=prepared_data)

    except Exception as e:
        # Handle any errors in the main execution flow with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error in main execution: {str(e)} at line {line_number}"
        )
        # Exit with error code 1 to indicate failure
        sys.exit(1)
