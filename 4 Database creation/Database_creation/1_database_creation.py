"""
Database creation script for EPL predictor project.

This script creates the PostgreSQL database tables for the football
prediction system, including league, club, match, and
club_season tables.
"""

# Standard library imports
import logging
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Third-party imports for database operations
import psycopg2
from psycopg2 import OperationalError

# Third-party imports for data processing
import pandas as pd


def setup_logging() -> None:
    """Configure logging for the database creation process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('database_creation.log'),
            logging.StreamHandler()
        ]
    )


def create_database_if_not_exists(
    *,
    db_name: str,
    db_connection_string: str
) -> None:
    """
    Create a database if it doesn't already exist.

    This function connects to the default 'postgres' database to create
    the target database, since you cannot create a database while
    connected to it.

    Args:
        db_name: Name of the database to create.
        db_connection_string: PostgreSQL connection string. The database
                            name in the string is replaced with 'postgres'
                            for the connection.
    """
    try:
        # Connect to the default 'postgres' database to create new database
        # Replace the database name in the connection string with 'postgres'
        conn = psycopg2.connect(db_connection_string)
        conn.autocommit = True  # Required for CREATE DATABASE
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            # Create the database
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logging.info(f"Created database {db_name}")
        else:
            logging.info(f"Database {db_name} already exists")
        
        cursor.close()
        conn.close()
        
    except OperationalError as e:
        logging.error(f"Database connection error while creating database: "
                     f"{e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while creating database: {e}")
        raise


def create_database_tables(*, db_connection_string: str) -> None:
    """
    Create database tables for the EPL predictor system.

    This function creates the following tables: league, football_match,
    club_season, club_history, and attendance_violin.

    Args:
        db_connection_string: PostgreSQL connection string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)

        cursor = conn.cursor()

        # Drop existing tables if they exist to ensure clean table creation
        # CASCADE ensures foreign key constraints are also dropped
        tables_to_drop = ['league', 'football_match',
                          'club_season', 'club_history', 'attendance_violin']
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            except Exception as e:
                logging.error(f"Error dropping table {table}: {e}")
                raise

        # Commit the DROP operations before creating new tables
        conn.commit()

        # Create the tables with proper formatting
        # Define SQL CREATE TABLE statements for each table
        # League table: stores league/season information
        create_statements = [
            """CREATE TABLE league (
                league_id VARCHAR(255) PRIMARY KEY NOT NULL,
                season VARCHAR(255) NOT NULL,
                league_tier INT NOT NULL,
                league_name VARCHAR(255) NOT NULL,
                season_start DATE NOT NULL,
                season_end DATE NOT NULL,
                league_size_matches INT NOT NULL,
                league_size_clubs INT NOT NULL,
                league_notes TEXT
            )""",
            # Football match table: stores individual match results and statistics
            # Foreign key reference to league table
            """CREATE TABLE football_match (
                match_id VARCHAR(255) PRIMARY KEY NOT NULL,
                league_id VARCHAR(255) NOT NULL REFERENCES league(league_id),
                match_date DATE NOT NULL,
                match_time VARCHAR(255),
                match_day_of_week VARCHAR(255) NOT NULL,
                attendance INT,
                home_club VARCHAR(255) NOT NULL,
                home_goals INT NOT NULL,
                home_fouls INT,
                home_yellow_cards INT,
                home_red_cards INT,
                away_club VARCHAR(255) NOT NULL,
                away_goals INT NOT NULL,
                away_fouls INT,
                away_yellow_cards INT,
                away_red_cards INT
            )""",
            # Club season table: stores club squad information for each season
            # Composite primary key via club_league_id
            """CREATE TABLE club_season (
                league_id VARCHAR(255) NOT NULL REFERENCES league(league_id),
                club_name VARCHAR(255) NOT NULL,
                club_league_id VARCHAR(255) NOT NULL PRIMARY KEY,
                squad_size INT,
                foreigner_count INT,
                foreigner_fraction DECIMAL,
                mean_age DECIMAL,
                total_market_value DECIMAL
            )""",
            # Club history table: tracks historical club name changes
            """CREATE TABLE club_history (
                club_name_year_changed_id VARCHAR(255) NOT NULL PRIMARY KEY,
                club_name VARCHAR(255) NOT NULL,
                nickname VARCHAR(255),
                modern_name VARCHAR(255) NOT NULL,
                year_changed INT NOT NULL,
                date_changed DATE,
                notes VARCHAR(255),
                wikipedia VARCHAR(255)
            )""",
            # Attendance violin table: stores probability density data for
            # attendance distributions by league
            """CREATE TABLE attendance_violin (
                attendance DECIMAL,
                probability_density DECIMAL,
                league_id VARCHAR(255) REFERENCES league(league_id) NOT NULL,
                attendance_league_id VARCHAR(255) NOT NULL PRIMARY KEY
            )"""
        ]

        # List of table names corresponding to create_statements
        table_names = ['league', 'football_match', 'club_season',
                       'club_history', 'attendance_violin']

        # Execute each CREATE TABLE statement
        for statement, table_name in zip(create_statements, table_names):
            try:
                cursor.execute(statement)
            except Exception as e:
                logging.error(f"Error creating table {table_name}: {e}")
                raise

        # Commit all table creation operations
        conn.commit()
        logging.info("All tables created successfully")

    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def load_database_table_football_match(
    *,
    db_connection_string: str
) -> None:
    """
    Load match data from CSV file into the football_match table.

    This function loads match data from Football_Match/Data/football_match.csv
    into the football_match table in PostgreSQL.

    Args:
        db_connection_string: PostgreSQL connection string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        logging.info("Successfully connected to database for football_match loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load match data from Match/Data/match.csv
        match_csv_path = (
            project_root /
            "Football_Match" /
            "Data" /
            "football_match.csv"
        )

        # Read the CSV file
        match_data = pd.read_csv(match_csv_path, low_memory=False)
        logging.info(f"Loaded {len(match_data)} match records from CSV")

        # Prepare data for insertion by creating tuples matching table columns
        # Order: match_id, league_id, match_date, match_time, match_day_of_week,
        # attendance, home_club, home_goals, home_fouls, home_yellow_cards,
        # home_red_cards, away_club, away_goals, away_fouls, away_yellow_cards,
        # away_red_cards
        match_records = [
            (
                row['match_id'],
                str(row['league_id']),  # Convert to string for consistency
                row['match_date'],
                # Handle NaN values for match_time
                row['match_time'] if pd.notna(row['match_time']) else None,
                row['match_day_of_week'],
                # Convert attendance to int, handle NaN
                int(row['attendance'])
                if pd.notna(row['attendance']) else None,
                row['home_club'],
                # Convert home_goals to int, handle NaN
                int(row['home_goals'])
                if pd.notna(row['home_goals']) else None,
                # Handle NaN for home_fouls
                int(row['home_fouls'])
                if pd.notna(row['home_fouls']) else None,
                # Handle NaN for home_yellow_cards
                int(row['home_yellow_cards'])
                if pd.notna(row['home_yellow_cards']) else None,
                # Handle NaN for home_red_cards
                int(row['home_red_cards'])
                if pd.notna(row['home_red_cards']) else None,
                row['away_club'],
                # Convert away_goals to int, handle NaN
                int(row['away_goals'])
                if pd.notna(row['away_goals']) else None,
                # Handle NaN for away_fouls
                int(row['away_fouls'])
                if pd.notna(row['away_fouls']) else None,
                # Handle NaN for away_yellow_cards
                int(row['away_yellow_cards'])
                if pd.notna(row['away_yellow_cards']) else None,
                # Handle NaN for away_red_cards
                int(row['away_red_cards'])
                if pd.notna(row['away_red_cards']) else None,

            )
            for _, row in match_data.iterrows()
        ]

        # Insert data into match table
        insert_query = """
            INSERT INTO football_match (match_id,
                league_id,
                match_date,
                match_time,
                match_day_of_week,
                attendance,
                home_club,
                home_goals,
                home_fouls,
                home_yellow_cards,
                home_red_cards,
                away_club,
                away_goals,
                away_fouls,
                away_yellow_cards,
                away_red_cards)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Execute bulk insert using executemany for better performance
        try:
            cursor.executemany(insert_query, match_records)
            conn.commit()
        except Exception as e:
            logging.error(
                f"Error inserting match records: {e}. "
                f"Total records attempted: {len(match_records)}"
            )
            conn.rollback()
            raise

        logging.info(f"Successfully loaded {len(match_records)} match "
                     "records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM football_match')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in match table: {count}")

    except FileNotFoundError as e:
        logging.error(f"football_match CSV file not found: {e}")
        raise
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during data loading: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logging.info("Database connection closed after data loading")


def load_database_table_league(*, db_connection_string: str) -> None:
    """
    Load league data from CSV file into the league table.

    This function loads league data from League/Data/league.csv into the
    league table in PostgreSQL.

    Args:
        db_connection_string: PostgreSQL connection string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        logging.info("Successfully connected to database for league data "
                     "loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load league data from League/Data/league.csv
        league_csv_path = (
            project_root /
            "League" /
            "Data" /
            "league.csv"
        )

        # Read the CSV file
        league_data = pd.read_csv(league_csv_path, low_memory=False)
        logging.info(f"Loaded {len(league_data)} league records from CSV")

        # Prepare data for insertion with proper type conversions
        # Order: league_id, season, league_tier, league_name, season_start,
        # season_end, league_size_matches, league_size_clubs, league_notes
        league_records = [
            (
                str(row['league_id']),  # Convert to string
                row['season'],
                int(row['league_tier']),  # Convert to integer
                row['league_name'],
                row['season_start'],
                row['season_end'],
                # Handle missing values for league_size_matches
                int(row['league_size_matches'])
                if pd.notna(row['league_size_matches']) else 0,
                # Handle missing values for league_size_clubs
                int(row['league_size_clubs'])
                if pd.notna(row['league_size_clubs']) else 0,
                # Handle missing values for league_notes
                row['league_notes'] if pd.notna(row['league_notes']) else None
            )
            for _, row in league_data.iterrows()
        ]

        # Insert data into league table with upsert logic
        # ON CONFLICT updates existing records if league_id already exists
        insert_query = """
            INSERT INTO league (
                league_id, season, league_tier, league_name,
                season_start, season_end, league_size_matches,
                league_size_clubs, league_notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (league_id) DO UPDATE SET
                season = EXCLUDED.season,
                league_tier = EXCLUDED.league_tier,
                league_name = EXCLUDED.league_name,
                season_start = EXCLUDED.season_start,
                season_end = EXCLUDED.season_end,
                league_size_matches = EXCLUDED.league_size_matches,
                league_size_clubs = EXCLUDED.league_size_clubs,
                league_notes = EXCLUDED.league_notes
        """

        # Execute batch insert
        cursor.executemany(insert_query, league_records)
        conn.commit()

        logging.info(f"Successfully loaded {len(league_records)} league "
                     "records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM "league"')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in league table: {count}")

    except FileNotFoundError as e:
        logging.error(f"League CSV file not found: {e}")
        raise
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during league data loading: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def load_database_table_club_season(*, db_connection_string: str) -> None:
    """
    Load club season data from CSV file into the club_season table.

    This function loads club season data from Club_Season/Data/club_season.csv
    into the club_season table in PostgreSQL.

    Args:
        db_connection_string: PostgreSQL connection string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        logging.info("Successfully connected to database for club season "
                     "data loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load club season data from Club_Season/Data/club_season.csv
        club_season_csv_path = (
            project_root /
            "Club_Season" /
            "Data" /
            "club_season.csv"
        )

        logging.info(f"Loading club season data from: {club_season_csv_path}")

        # Read the CSV file
        club_season_data = pd.read_csv(club_season_csv_path, low_memory=False)
        logging.info(f"Loaded {len(club_season_data)} club season records "
                     "from CSV")

        # Prepare data for insertion with proper type conversions and
        # null handling
        # Order: league_id, club_name, club_league_id, squad_size,
        # foreigner_count, foreigner_fraction, mean_age, total_market_value
        club_season_records = [
            (
                str(row['league_id']),  # Convert to string
                row['club_name'],
                str(row['club_league_id']),  # Convert to string
                # Handle missing values for squad_size
                int(row['squad_size'])
                if pd.notna(row['squad_size']) else None,
                # Handle missing values for foreigner_count
                int(row['foreigner_count'])
                if pd.notna(row['foreigner_count']) else None,
                # Handle missing values for foreigner_fraction
                float(row['foreigner_fraction'])
                if pd.notna(row['foreigner_fraction']) else None,
                # Handle missing values for mean_age
                float(row['mean_age'])
                if pd.notna(row['mean_age']) else None,
                # Handle missing values for total_market_value
                float(row['total_market_value'])
                if pd.notna(row['total_market_value']) else None
            )
            for _, row in club_season_data.iterrows()
        ]

        # Insert data into club_season table
        # ON CONFLICT DO NOTHING skips duplicate records based on primary key
        insert_query = """
            INSERT INTO club_season (
                league_id, club_name, club_league_id, squad_size,
                foreigner_count, foreigner_fraction, mean_age,
                total_market_value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """

        # Execute batch insert
        cursor.executemany(insert_query, club_season_records)
        conn.commit()

        logging.info(f"Successfully loaded {len(club_season_records)} club "
                     "season records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM "club_season"')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in club_season table: {count}")

    except FileNotFoundError as e:
        logging.error(f"Club season CSV file not found: {e}")
        raise
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during club season data loading: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logging.info("Database connection closed after club season data "
                         "loading")





def load_database_table_club_history(*, db_connection_string: str) -> None:
    """
    Load club history data from CSV file into the club_history table.

    This function loads club history data from Club_History/Data/
    club_history.csv into the club_history table in PostgreSQL.

    Args:
        db_connection_string: PostgreSQL connection string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        logging.info("Successfully connected to database for club history "
                     "data loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load club history data from Club_History/Data/club_history.csv
        club_history_csv_path = (
            project_root /
            "Club_History" /
            "Data" /
            "club_history.csv"
        )

        logging.info(f"Loading club history data from: "
                     f"{club_history_csv_path}")

        # Read the CSV file
        club_history_data = pd.read_csv(club_history_csv_path,
                                        low_memory=False)
        logging.info(f"Loaded {len(club_history_data)} club history records "
                     "from CSV")

        # Prepare data for insertion with special handling for date_changed
        # Order: club_name_year_changed_id, club_name, nickname, modern_name,
        # year_changed, date_changed, notes, wikipedia
        club_history_records = []
        for _, row in club_history_data.iterrows():
            # Handle date_changed with potential invalid formats
            # Some dates may have '=' instead of '-' separators
            date_changed = None
            if pd.notna(row['date_changed']):
                try:
                    # Try to parse the date, handle common format issues
                    date_str = str(row['date_changed']).replace('=', '-')
                    if date_str and date_str != 'nan':
                        # Validate date format (YYYY-MM-DD)
                        from datetime import datetime
                        datetime.strptime(date_str, '%Y-%m-%d')
                        date_changed = date_str
                except (ValueError, TypeError):
                    # If date parsing fails, set to None
                    date_changed = None

            # Build record tuple with null handling
            club_history_records.append((
                row['club_name_year_changed_id'],
                row['club_name'],
                row['nickname'] if pd.notna(row['nickname']) else None,
                row['modern_name'],
                # Convert year_changed to int, default to 0 if missing
                int(row['year_changed'])
                if pd.notna(row['year_changed']) else 0,
                date_changed,  # Already handled above
                row['notes'] if pd.notna(row['notes']) else None,
                row['wikipedia'] if pd.notna(row['wikipedia']) else None
            ))

        # Insert data into club_history table
        insert_query = """
            INSERT INTO club_history (
                club_name_year_changed_id, 
                club_name, 
                nickname, 
                modern_name, 
                year_changed,
                date_changed, 
                notes, 
                wikipedia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Execute batch insert
        cursor.executemany(insert_query, club_history_records)
        conn.commit()

        logging.info(f"Successfully loaded {len(club_history_records)} club "
                     "history records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM "club_history"')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in club_history table: {count}")

    except FileNotFoundError as e:
        logging.error(f"Club history CSV file not found: {e}")
        raise
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during club history data "
                      f"loading: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logging.info("Database connection closed after club history data "
                         "loading")


def load_database_table_attendance_violin(
    *,
    db_connection_string: str
) -> None:
    """
    Load attendance violin data from CSV file into the attendance_violin 
    table.

    This function loads attendance violin data from 
    Attendance_violin/Data/attendance_violin.csv into the attendance_violin
    table in PostgreSQL.

    Args:
        db_connection_string: PostgreSQL connection string.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(db_connection_string)
        logging.info("Successfully connected to database for attendance "
                     "violin data loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load attendance violin data from 
        # Attendance_violin/Data/attendance_violin.csv
        attendance_violin_csv_path = (
            project_root /
            "Attendance_violin" /
            "Data" /
            "attendance_violin.csv"
        )

        logging.info(f"Loading attendance violin data from: "
                     f"{attendance_violin_csv_path}")

        # Read the CSV file
        attendance_violin_data = pd.read_csv(
            attendance_violin_csv_path,
            low_memory=False
        )
        logging.info(f"Loaded {len(attendance_violin_data)} attendance "
                     "violin records from CSV")

        # Prepare data for insertion with type conversions
        # Order: attendance, probability_density, league_id,
        # attendance_league_id
        attendance_violin_records = [
            (
                float(row['attendance']),  # Convert to float
                float(row['probability_density']),  # Convert to float
                str(row['league_id']),  # Convert to string
                str(row['attendance_league_id'])  # Convert to string
            )
            for _, row in attendance_violin_data.iterrows()
        ]

        # Insert data into attendance_violin table
        insert_query = """
            INSERT INTO attendance_violin (
                attendance, 
                probability_density, 
                league_id,
                attendance_league_id
            )
            VALUES (%s, %s, %s, %s)
        """

        # Execute batch insert
        cursor.executemany(insert_query, attendance_violin_records)
        conn.commit()

        logging.info(f"Successfully loaded {len(attendance_violin_records)} "
                     "attendance violin records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM "attendance_violin"')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in attendance_violin table: {count}")

    except FileNotFoundError as e:
        logging.error(f"Attendance violin CSV file not found: {e}")
        raise
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during attendance violin data "
                      f"loading: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logging.info("Database connection closed after attendance violin "
                         "data loading")


if __name__ == "__main__":
    # Initialize logging before any operations
    setup_logging()

    # Are we running the script to populate the local or the remote database?
    local = True

    logging.info(f"Running script to populate the {'local' if local else 'remote'} database")

    try:
        # Get the current script's directory and navigate to Django app folder
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        django_app_path = project_root / "5 Django app"
        env_path = django_app_path / ".env"
        
        if not env_path.exists():
            raise FileNotFoundError(
                f".env file not found at: {env_path}. "
                f"Please ensure the file exists in the Django app folder."
            )
        
        load_dotenv(dotenv_path=env_path)

        # Set either DATABASE_URL_REMOTE or DATABASE_URL_LOCAL environment variable
        database_url_key = 'DATABASE_URL_LOCAL' if local else 'DATABASE_URL_REMOTE'
        db_connection_string = os.environ.get(database_url_key)

        if not db_connection_string:
            raise ValueError(
                f"{database_url_key} environment variable is not set in the "
                ".env file"
            )
        
        # Extract database name from connection string for database creation
        # Format: postgresql://user:password@host:port/database
        db_name_match = re.search(r'/([^/]+)$', db_connection_string)
        db_name = db_name_match.group(1)

        # Step 0: Create database if it doesn't exist
        create_database_if_not_exists(
            db_name=db_name,
            db_connection_string=db_connection_string
        )
        
        # Step 1: Create all database tables
        create_database_tables(db_connection_string=db_connection_string)

        # Step 2: Load league data (must be loaded first due to foreign keys)
        load_database_table_league(db_connection_string=db_connection_string)

        # Step 3: Load match data (depends on league table)
        load_database_table_football_match(db_connection_string=db_connection_string)

        # Step 4: Load club history data
        load_database_table_club_history(db_connection_string=db_connection_string)

        # Step 5: Load attendance violin data (depends on league table)
        load_database_table_attendance_violin(
            db_connection_string=db_connection_string
        )

        # Step 6: Load club season data (depends on league table)
        load_database_table_club_season(db_connection_string=db_connection_string)

        logging.info("All data loading completed successfully")

    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        raise
