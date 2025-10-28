"""
Database creation script for EPL predictor project.

This script creates the PostgreSQL database tables for the football
prediction system, including league, club, match, club_match, and
club_season tables.
"""

import logging
import psycopg2
from psycopg2 import OperationalError
import pandas as pd
import os
from pathlib import Path


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


def create_database_tables(*, connection_params: dict) -> None:
    """
    Create database tables for the EPL predictor system.

    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**connection_params)
        logging.info("Successfully connected to database")

        cursor = conn.cursor()

        # Drop existing tables if they exist
        tables_to_drop = ['league', 'match', 'club_match',
                          'club_season', 'club_history']
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                logging.info(f"Dropped table {table} if it existed")
            except Exception as e:
                logging.error(f"Error dropping table {table}: {e}")
                raise

        conn.commit()

        # Create the tables with proper formatting
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
            """CREATE TABLE "match" (
                match_id VARCHAR(255) PRIMARY KEY NOT NULL,
                league_id VARCHAR(255) NOT NULL,
                match_date DATE NOT NULL,
                attendance INT NOT NULL
            )""",
            """CREATE TABLE club_match (
                match_id VARCHAR(255) NOT NULL,
                club_name VARCHAR(255) NOT NULL,
                goals INT NOT NULL,
                red_cards INT,
                yellow_cards INT,
                fouls INT,
                is_home BOOLEAN NOT NULL
            )""",
            """CREATE TABLE club_season (
                league_id VARCHAR(255) NOT NULL,
                club_name VARCHAR(255) NOT NULL,
                squad_size INT,
                foreigner_count INT,
                foreigner_fraction DECIMAL,
                mean_age DECIMAL,
                total_market_value DECIMAL
            )""",
            """CREATE TABLE club_history (
                club_name VARCHAR(255) NOT NULL,
                nickname VARCHAR(255),
                modern_name VARCHAR(255) NOT NULL,
                year_changed INT NOT NULL,
                date_changed DATE,
                notes VARCHAR(255),
                wikipedia VARCHAR(255)
            )"""
        ]

        table_names = ['league', 'match', 'club_match', 'club_season',
                       'club_history']

        for statement, table_name in zip(create_statements, table_names):
            try:
                cursor.execute(statement)
                logging.info(f"Successfully created table {table_name}")
            except Exception as e:
                logging.error(f"Error creating table {table_name}: {e}")
                raise

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
            logging.info("Database connection closed")


def load_database_table_match(*, connection_params: dict) -> None:
    """
    Load match data from CSV file into the match table.

    This function loads match data from Match/Data/match.csv into the
    match table in PostgreSQL.

    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**connection_params)
        logging.info("Successfully connected to database for data loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load match data from Match/Data/match.csv
        match_csv_path = (
            project_root /
            "Match" /
            "Data" /
            "match.csv"
        )

        logging.info(f"Loading match data from: {match_csv_path}")

        # Read the CSV file
        match_data = pd.read_csv(match_csv_path, low_memory=False)
        logging.info(f"Loaded {len(match_data)} match records from CSV")

        # Prepare data for insertion
        match_records = [
            (
                row['match_id'],
                str(row['league_id']),
                row['match_date'],
                int(row['attendance']) if pd.notna(row['attendance']) else 0
            )
            for _, row in match_data.iterrows()
        ]

        # Insert data into match table
        insert_query = """
            INSERT INTO "match" (match_id, league_id, match_date, attendance)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (match_id) DO UPDATE SET
                league_id = EXCLUDED.league_id,
                match_date = EXCLUDED.match_date,
                attendance = EXCLUDED.attendance
        """

        # Execute batch insert
        cursor.executemany(insert_query, match_records)
        conn.commit()

        logging.info(f"Successfully loaded {len(match_records)} match "
                     "records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM "match"')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in match table: {count}")

    except FileNotFoundError as e:
        logging.error(f"CSV file not found: {e}")
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


def load_database_table_league(*, connection_params: dict) -> None:
    """
    Load league data from CSV file into the league table.

    This function loads league data from League/Data/league.csv into the
    league table in PostgreSQL.

    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**connection_params)
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

        logging.info(f"Loading league data from: {league_csv_path}")

        # Read the CSV file
        league_data = pd.read_csv(league_csv_path, low_memory=False)
        logging.info(f"Loaded {len(league_data)} league records from CSV")

        # Prepare data for insertion
        league_records = [
            (
                str(row['league_id']),
                row['season'],
                int(row['league_tier']),
                row['league_name'],
                row['season_start'],
                row['season_end'],
                int(row['league_size_matches'])
                if pd.notna(row['league_size_matches']) else 0,
                int(row['league_size_clubs'])
                if pd.notna(row['league_size_clubs']) else 0,
                row['league_notes'] if pd.notna(row['league_notes']) else None
            )
            for _, row in league_data.iterrows()
        ]

        # Insert data into league table
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
            logging.info("Database connection closed after league data "
                         "loading")


def load_database_table_club_season(*, connection_params: dict) -> None:
    """
    Load club season data from CSV file into the club_season table.

    This function loads club season data from Club_Season/Data/club_season.csv
    into the club_season table in PostgreSQL.

    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**connection_params)
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

        # Prepare data for insertion
        club_season_records = [
            (
                str(row['league_id']),
                row['club_name'],
                int(row['squad_size'])
                if pd.notna(row['squad_size']) else None,
                int(row['foreigner_count'])
                if pd.notna(row['foreigner_count']) else None,
                float(row['foreigner_fraction'])
                if pd.notna(row['foreigner_fraction']) else None,
                float(row['mean_age'])
                if pd.notna(row['mean_age']) else None,
                float(row['total_market_value'])
                if pd.notna(row['total_market_value']) else None
            )
            for _, row in club_season_data.iterrows()
        ]

        # Insert data into club_season table
        insert_query = """
            INSERT INTO club_season (
                league_id, club_name, squad_size, foreigner_count,
                foreigner_fraction, mean_age, total_market_value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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


def load_database_table_club_match(*, connection_params: dict) -> None:
    """
    Load club match data from CSV file into the club_match table.

    This function loads club match data from Club_Match/Data/club_match.csv
    into the club_match table in PostgreSQL.

    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**connection_params)
        logging.info("Successfully connected to database for club match "
                     "data loading")

        cursor = conn.cursor()

        # Find the project root by looking for the script's location
        script_dir = Path(__file__).parent
        # Go up one level from Database_creation
        project_root = script_dir.parent

        # Load club match data from Club_Match/Data/club_match.csv
        club_match_csv_path = (
            project_root /
            "Club_Match" /
            "Data" /
            "club_match.csv"
        )

        logging.info(f"Loading club match data from: {club_match_csv_path}")

        # Read the CSV file
        club_match_data = pd.read_csv(club_match_csv_path, low_memory=False)
        logging.info(f"Loaded {len(club_match_data)} club match records "
                     "from CSV")

        # Prepare data for insertion with proper column mapping
        club_match_records = [
            (
                row['match_id'],  # Use actual match_id from CSV
                row['club_name'],
                int(row['goals']) if pd.notna(row['goals']) else 0,
                int(row['red_cards'])
                if pd.notna(row['red_cards']) else None,
                int(row['yellow_cards'])
                if pd.notna(row['yellow_cards']) else None,
                int(row['fouls'])
                if pd.notna(row['fouls']) else None,
                bool(row['is_home'])
                if pd.notna(row['is_home']) else False
            )
            for _, row in club_match_data.iterrows()
        ]

        # Insert data into club_match table
        insert_query = """
            INSERT INTO club_match (
                match_id, club_name, goals, red_cards,
                yellow_cards, fouls, is_home
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        # Execute batch insert
        cursor.executemany(insert_query, club_match_records)
        conn.commit()

        logging.info(f"Successfully loaded {len(club_match_records)} club "
                     "match records into database")

        # Verify the data was loaded
        cursor.execute('SELECT COUNT(*) FROM "club_match"')
        count = cursor.fetchone()[0]
        logging.info(f"Total records in club_match table: {count}")

    except FileNotFoundError as e:
        logging.error(f"Club match CSV file not found: {e}")
        raise
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during club match data loading: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            logging.info("Database connection closed after club match data "
                         "loading")


def load_database_table_club_history(*, connection_params: dict) -> None:
    """
    Load club history data from CSV file into the club_history table.

    This function loads club history data from Club_History/Data/
    club_history.csv into the club_history table in PostgreSQL.

    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        # Connect to the database
        conn = psycopg2.connect(**connection_params)
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

        # Prepare data for insertion
        club_history_records = []
        for _, row in club_history_data.iterrows():
            # Handle date_changed with potential invalid formats
            date_changed = None
            if pd.notna(row['date_changed']):
                try:
                    # Try to parse the date, handle common format issues
                    date_str = str(row['date_changed']).replace('=', '-')
                    if date_str and date_str != 'nan':
                        # Validate date format
                        from datetime import datetime
                        datetime.strptime(date_str, '%Y-%m-%d')
                        date_changed = date_str
                except (ValueError, TypeError):
                    # If date parsing fails, set to None
                    date_changed = None

            club_history_records.append((
                row['club_name'],
                row['nickname'] if pd.notna(row['nickname']) else None,
                row['modern_name'],
                int(row['year_changed'])
                if pd.notna(row['year_changed']) else 0,
                date_changed,
                row['notes'] if pd.notna(row['notes']) else None,
                row['wikipedia'] if pd.notna(row['wikipedia']) else None
            ))

        # Insert data into club_history table
        insert_query = """
            INSERT INTO club_history (
                club_name, nickname, modern_name, year_changed,
                date_changed, notes, wikipedia
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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


if __name__ == "__main__":
    setup_logging()

    # Database connection parameters
    connection_params = {
        'host': os.environ['FOOTBALL_HOST'],
        'port': int(os.environ['FOOTBALL_PORT']),
        'database': "Football",
        'user': os.environ['FOOTBALL_USER'],
        'password': os.environ['FOOTBALL_PASSWORD']
    }

    try:
        create_database_tables(connection_params=connection_params)
        logging.info("Database creation completed successfully")

        # Load match data into the table
        load_database_table_match(connection_params=connection_params)
        logging.info("Match data loading completed successfully")

        # Load league data into the table
        load_database_table_league(connection_params=connection_params)
        logging.info("League data loading completed successfully")

        # Load club season data into the table
        load_database_table_club_season(connection_params=connection_params)
        logging.info("Club season data loading completed successfully")

        # Load club history data into the table
        load_database_table_club_history(connection_params=connection_params)
        logging.info("Club history data loading completed successfully")

        # Load club match data into the table
        load_database_table_club_match(connection_params=connection_params)
        logging.info("Club match data loading completed successfully")

    except Exception as e:
        logging.error(f"Database operation failed: {e}")
        raise
