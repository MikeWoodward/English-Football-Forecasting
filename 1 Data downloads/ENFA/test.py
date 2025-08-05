#!/usr/bin/env python3
"""Test script to read ENFA cleansed data.

This script simply reads the enfa_cleansed.csv file from the Data folder
and does nothing else with it.
"""

import pandas as pd
from pathlib import Path


if __name__ == "__main__":
    # Read the enfa_cleansed.csv file from the Data folder
    enfa_cleansed = pd.read_csv("Data/enfa_cleansed.csv") 

    test1 = enfa_cleansed[(enfa_cleansed['season'] == '2018-2019') & (enfa_cleansed['league_tier'] == 2)]

    print(test1.shape)

    test1.groupby('home_club').count()
