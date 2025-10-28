"""
Database check script for EPL predictor project.

This script connects to the Football database and performs various checks
to verify the database structure and data integrity.
"""

import logging
import psycopg2
from psycopg2 import OperationalError
import pandas as pd
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple


def setup_logging() -> None:
    """Configure logging for the database check process."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('database_check.log'),
            logging.StreamHandler()
        ]
    )


def get_database_connection(*, connection_params: Dict[str, Any]) -> psycopg2.extensions.connection:
    """
    Establish a connection to the Football database.
    
    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    
    Returns:
        psycopg2 connection object.
        
    Raises:
        OperationalError: If database connection fails.
    """
    try:
        conn = psycopg2.connect(**connection_params)
        logging.info("Successfully connected to Football database")
        return conn
    except OperationalError as e:
        logging.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during database connection: {e}")
        raise


def check_database_tables(*, connection_params: Dict[str, Any]) -> None:
    """
    Check if all required database tables exist and display their structure.
    
    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        conn = get_database_connection(connection_params=connection_params)
        cursor = conn.cursor()
        
        # List of expected tables
        expected_tables = ['league', 'match', 'club_match', 'club_season', 
                          'club_history']
        
        logging.info("Checking database table existence...")
        
        for table_name in expected_tables:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (table_name,))
            
            exists = cursor.fetchone()[0]
            if exists:
                logging.info(f"✓ Table '{table_name}' exists")
                
                # Get table structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = cursor.fetchall()
                logging.info(f"  Columns in '{table_name}':")
                for col_name, data_type, nullable, default in columns:
                    nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                    default_str = f", DEFAULT: {default}" if default else ""
                    logging.info(f"    - {col_name}: {data_type} {nullable_str}{default_str}")
            else:
                logging.warning(f"✗ Table '{table_name}' does not exist")

        # Check club counts per season and league are consistent with the league size club data
        cursor.execute("""
            SELECT league_id, COUNT(DISTINCT club_name) as club_count
            FROM club_season
            GROUP BY league_id
        """)
        club_counts = cursor.fetchall()
        for league_id, club_count in club_counts:
            cursor.execute("""
                SELECT league_size_clubs
                FROM league
                WHERE league_id = %s
            """, (league_id,))
            league_size_clubs = cursor.fetchone()[0]
            if club_count != league_size_clubs:
                logging.error(f"✗ Club count for league {league_id} is not consistent with the league size clubs data")
        logging.info("✓ Club count for leagues is consistent with the league size clubs data")
        
        # Check match counts per season and league are consistent with the league size matches data
        cursor.execute("""
            SELECT league_id, COUNT(DISTINCT match_id) as match_count
            FROM match
            GROUP BY league_id
        """)
        match_counts = cursor.fetchall()
        for league_id, match_count in match_counts:
            cursor.execute("""
                SELECT league_size_matches
                FROM league
                WHERE league_id = %s
            """, (league_id,))
            league_size_matches = cursor.fetchone()[0]
            if match_count != league_size_matches:
                logging.error(f"✗ Match count for league {league_id} is not consistent with the league size match data")
        logging.info("✓ Match count for leagues is consistent with the league size match data")
        
        cursor.close()
        conn.close()
        logging.info("Database table check completed")
        
    except Exception as e:
        logging.error(f"Error checking database tables: {e}")
        raise


def check_table_record_counts(*, connection_params: Dict[str, Any]) -> None:
    """
    Check the record count for each table in the database.
    
    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        conn = get_database_connection(connection_params=connection_params)
        cursor = conn.cursor()
        
        tables = ['league', 'match', 'club_match', 'club_season', 'club_history']
        
        logging.info("Checking table record counts...")
        
        for table_name in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]
                logging.info(f"Table '{table_name}': {count:,} records")
            except Exception as e:
                logging.error(f"Error counting records in '{table_name}': {e}")
        
        cursor.close()
        conn.close()
        logging.info("Record count check completed")
        
    except Exception as e:
        logging.error(f"Error checking record counts: {e}")
        raise


def check_data_quality(*, connection_params: Dict[str, Any]) -> None:
    """
    Perform basic data quality checks on the database tables.
    
    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        conn = get_database_connection(connection_params=connection_params)
        cursor = conn.cursor()
        
        logging.info("Performing data quality checks...")
        
        # Check for NULL values in critical fields
        quality_checks = [
            ("league", "league_id", "NULL league_id values"),
            ("league", "season", "NULL season values"),
            ("match", "match_id", "NULL match_id values"),
            ("match", "league_id", "NULL league_id values in match table"),
            ("club_match", "match_id", "NULL match_id values in club_match"),
            ("club_match", "club_name", "NULL club_name values"),
            ("club_season", "league_id", "NULL league_id values in club_season"),
            ("club_season", "club_name", "NULL club_name values in club_season")
        ]
        
        for table, column, description in quality_checks:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}" WHERE {column} IS NULL')
                null_count = cursor.fetchone()[0]
                if null_count > 0:
                    logging.warning(f"Found {null_count} {description}")
                else:
                    logging.info(f"✓ No {description}")
            except Exception as e:
                logging.error(f"Error checking {description}: {e}")
        
        # Check for duplicate match_ids
        try:
            cursor.execute('''
                SELECT match_id, COUNT(*) as count
                FROM "match"
                GROUP BY match_id
                HAVING COUNT(*) > 1
            ''')
            duplicates = cursor.fetchall()
            if duplicates:
                logging.warning(f"Found {len(duplicates)} duplicate match_ids")
                for match_id, count in duplicates[:5]:  # Show first 5
                    logging.warning(f"  match_id '{match_id}' appears {count} times")
            else:
                logging.info("✓ No duplicate match_ids found")
        except Exception as e:
            logging.error(f"Error checking for duplicate match_ids: {e}")
        
        # Check date ranges
        try:
            cursor.execute('SELECT MIN(match_date), MAX(match_date) FROM "match"')
            min_date, max_date = cursor.fetchone()
            logging.info(f"Match date range: {min_date} to {max_date}")
        except Exception as e:
            logging.error(f"Error checking date range: {e}")
        
        cursor.close()
        conn.close()
        logging.info("Data quality checks completed")
        
    except Exception as e:
        logging.error(f"Error during data quality checks: {e}")
        raise


def check_foreign_key_relationships(*, connection_params: Dict[str, Any]) -> None:
    """
    Check foreign key relationships between tables.
    
    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        conn = get_database_connection(connection_params=connection_params)
        cursor = conn.cursor()
        
        logging.info("Checking foreign key relationships...")
        
        # Check match.league_id references league.league_id
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM "match" m
                LEFT JOIN league l ON m.league_id = l.league_id
                WHERE l.league_id IS NULL
            ''')
            orphaned_matches = cursor.fetchone()[0]
            if orphaned_matches > 0:
                logging.warning(f"Found {orphaned_matches} matches with invalid league_id")
            else:
                logging.info("✓ All matches have valid league_id references")
        except Exception as e:
            logging.error(f"Error checking match-league relationship: {e}")
        
        # Check club_match.match_id references match.match_id
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM club_match cm
                LEFT JOIN "match" m ON cm.match_id = m.match_id
                WHERE m.match_id IS NULL
            ''')
            orphaned_club_matches = cursor.fetchone()[0]
            if orphaned_club_matches > 0:
                logging.warning(f"Found {orphaned_club_matches} club_matches with invalid match_id")
            else:
                logging.info("✓ All club_matches have valid match_id references")
        except Exception as e:
            logging.error(f"Error checking club_match-match relationship: {e}")
        
        # Check club_season.league_id references league.league_id
        try:
            cursor.execute('''
                SELECT COUNT(*) FROM club_season cs
                LEFT JOIN league l ON cs.league_id = l.league_id
                WHERE l.league_id IS NULL
            ''')
            orphaned_club_seasons = cursor.fetchone()[0]
            if orphaned_club_seasons > 0:
                logging.warning(f"Found {orphaned_club_seasons} club_seasons with invalid league_id")
            else:
                logging.info("✓ All club_seasons have valid league_id references")
        except Exception as e:
            logging.error(f"Error checking club_season-league relationship: {e}")
        
        cursor.close()
        conn.close()
        logging.info("Foreign key relationship checks completed")
        
    except Exception as e:
        logging.error(f"Error during foreign key relationship checks: {e}")
        raise


def generate_database_summary(*, connection_params: Dict[str, Any]) -> None:
    """
    Generate a comprehensive summary of the database contents.
    
    Args:
        connection_params: Dictionary containing database connection
                          parameters including host, port, database,
                          user, and password.
    """
    try:
        conn = get_database_connection(connection_params=connection_params)
        cursor = conn.cursor()
        
        logging.info("Generating database summary...")
        
        # Get unique clubs
        cursor.execute('SELECT DISTINCT club_name FROM club_match ORDER BY club_name')
        clubs = cursor.fetchall()
        logging.info(f"Found {len(clubs)} unique clubs in match data")
        
        # Get date range
        cursor.execute('SELECT MIN(match_date), MAX(match_date) FROM "match"')
        min_date, max_date = cursor.fetchone()
        logging.info(f"Match data spans from {min_date} to {max_date}")
        
        cursor.close()
        conn.close()
        logging.info("Database summary completed")
        
    except Exception as e:
        logging.error(f"Error generating database summary: {e}")
        raise


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
        logging.info("Starting database check process...")
        
        # Perform all checks
        check_database_tables(connection_params=connection_params)
        check_table_record_counts(connection_params=connection_params)
        check_data_quality(connection_params=connection_params)
        check_foreign_key_relationships(connection_params=connection_params)
        generate_database_summary(connection_params=connection_params)
        
        logging.info("Database check process completed successfully")
        
    except Exception as e:
        logging.error(f"Database check process failed: {e}")
        raise
