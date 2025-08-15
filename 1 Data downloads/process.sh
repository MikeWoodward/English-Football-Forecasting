#!/bin/bash

# =============================================================================
# English League Football Data Processing Pipeline Script
# =============================================================================
# This script orchestrates the processing of multiple football data sources
# for the English League predictor project. It handles data consolidation
# and cleansing operations across various data providers.
#
# Data Sources Processed:
# - ENFA (English National Football Archive)
# - English Football League Tables
# - FBRef (Football Reference)
# - FootballData.co.uk
# - Todor
# - TransferMarkt
#
# Author: Data Science Team
# Date: $(date)
# =============================================================================

echo "Starting English League Football Data Processing Pipeline..."
echo "=========================================================="
echo

# =============================================================================
# ENFA (English National Football Archive) Data Processing
# =============================================================================
echo "Processing ENFA data..."
echo "----------------------"

# Change to ENFA directory to ensure scripts run from correct location
cd ENFA

# Step 1: Consolidate ENFA match data from HTML files
# This step consolidates match data from HTML files into structured format
# Processes raw HTML data from the ENFA archive into a consolidated dataset
echo "Step 1: Consolidating ENFA match data from HTML files..."
python3 2_enfa_consolidate.py
if [ $? -ne 0 ]; then
    echo "Error: ENFA consolidate script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "ENFA consolidate script completed successfully."
echo

# Step 2: Cleanse and validate the consolidated ENFA data
# This step performs data validation, removes duplicates, and standardizes formats
echo "Step 2: Cleansing and validating ENFA data..."
python3 3_enfa_cleanse.py
if [ $? -ne 0 ]; then
    echo "Error: ENFA cleanse script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "ENFA cleanse script completed successfully."
echo

echo "ENFA data processing completed successfully!"
echo

# Return to the parent directory
cd ..

# =============================================================================
# English Football League Tables Data Processing
# =============================================================================
echo "Processing English Football League Tables data..."
echo "-----------------------------------------------"

# Change to the EnglishFootballLeagueTables directory
cd EnglishFootballLeagueTables

# Step 1: Extract match data from English Football League Tables
# This step processes HTML files to extract match information and statistics
echo "Step 1: Extracting match data from English Football League Tables..."
python3 2_englishfootballleaguetables_matches.py
if [ $? -ne 0 ]; then
    echo "Error: English Football League Tables extraction script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "English Football League Tables extraction completed successfully."
echo

# Step 2: Cleanse and standardize the extracted match data
# This step validates data integrity, removes inconsistencies, and standardizes formats
echo "Step 2: Cleansing English Football League Tables match data..."
python3 3_cleanse_englishfootballleaguetables_matches.py
if [ $? -ne 0 ]; then
    echo "Error: English Football League Tables cleanse script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "English Football League Tables cleansing completed successfully."
echo

# Return to the parent directory
cd ..

# =============================================================================
# FBRef (Football Reference) Data Processing
# =============================================================================
echo "Processing FBRef data..."
echo "------------------------"

# Change to the FBRef directory
cd FBRef

# Step 1: Cleanse and standardize the FBRef data
# This step validates data integrity, removes inconsistencies, and standardizes formats
echo "Step 1: Cleansing FBRef match data..."
python3 2_FBRef_cleanse.py
if [ $? -ne 0 ]; then
    echo "Error: FBRef cleanse script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "FBRef cleansing completed successfully."
echo

# Return to the parent directory
cd ..

# =============================================================================
# FootballData.co.uk Data Processing
# =============================================================================
echo "Processing FootballData data..."
echo "-------------------------------------"

# Change to the FootballData directory
cd FootballData


# Step 1: Process and standardize the FootballData.co.uk data
# This step processes raw API data into structured match information
echo "Step 1: Processing FootballData.co.uk match data..."
python3 2_football-data_process.py
if [ $? -ne 0 ]; then
    echo "Error: FootballData processing script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "FootballData processing completed successfully."
echo

# Return to the parent directory
cd ..

# =============================================================================
# Todor Data Processing
# =============================================================================
echo "Processing Todor data..."
echo "------------------------"

# Change to the Todor directory
cd Todor


# Step 1: Extract match data from Todor tables
# This step processes HTML tables to extract match information and statistics
echo "Step 1: Extracting match data from Todor tables..."
python3 2_todor_get_data.py
if [ $? -ne 0 ]; then
    echo "Error: Todor extraction script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "Todor extraction completed successfully."
echo
    
# Step 2: Cleanse and standardize the extracted Todor data
# This step validates data integrity, removes inconsistencies, and standardizes formats
echo "Step 2: Cleansing Todor match data..."
python3 3_todor_cleanse.py
if [ $? -ne 0 ]; then
    echo "Error: Todor cleanse script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "Todor cleansing completed successfully."
echo

# Return to the parent directory
cd ..
    
# =============================================================================
# TransferMarkt-values Data Processing
# =============================================================================
echo "Processing TransferMarkt-values data..."
echo "-------------------------------------"

# Change to the TransferMarkt-values directory
cd TransferMarkt-values


# Step 1: Process and standardize the TransferMarkt data
# This step processes raw market value data into structured team valuations
echo "Step 1: Processing TransferMarkt market value data..."
python3 2_transfermarkt_process.py
if [ $? -ne 0 ]; then
    echo "Error: TransferMarkt processing script failed with exit code $?"
    read -p "Press Enter to continue..."
    exit $?
fi
echo "TransferMarkt processing completed successfully."
echo

# Return to the parent directory
cd ..

# =============================================================================
# Script Completion
# =============================================================================
echo "=========================================================="
echo "English League Football Data Processing Pipeline completed!"
echo "=========================================================="
echo
echo "Processed data sources:"
echo "- ENFA (English National Football Archive)"
echo "- English Football League Tables"
echo "- FBRef (Football Reference)"
echo "- FootballData.co.uk"
echo "- Todor"
echo "- TransferMarkt-values"
echo
echo "Next steps:"
echo "- Review processed data in respective Data/ directories"
echo "- Run additional data source processing scripts as needed"
echo "- Proceed to data integration and analysis phase"
echo

# Wait for user acknowledgment before exiting
read -p "Press Enter to continue..."
