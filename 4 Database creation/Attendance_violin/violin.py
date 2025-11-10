#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 30 17:11:36 2025

@author: mikewoodward
"""

# %%---------------------------------------------------------------------------
# Module metadata
# -----------------------------------------------------------------------------
__author__ = "mikewoodward"
__license__ = "MIT"
__summary__ = "One line summary"

# %%---------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import psycopg2
import pandas as pd
import numpy as np
import pandas
import scipy

# Bokeh imports for interactive plotting and visualization
from bokeh.plotting import figure
from bokeh.io import show
from bokeh.layouts import column

from bokeh.models import (
    ColumnDataSource, CustomJS, Slider, ColorBar, LinearColorMapper, Div, HoverTool
)

# %%---------------------------------------------------------------------------
# Function name
# -----------------------------------------------------------------------------
def attendance(connection_params):
    """Function description."""

    # Open the csv file football_match.csv
    football_match_data = pd.read_csv('Football_Match/Data/football_match.csv')
    # Remove rows where attendance is null
    football_match_data = football_match_data[football_match_data['attendance'].notnull()][['league_id', 'attendance']].drop_duplicates()
    return football_match_data
  
def get_kdes(data):
  kdes = []
  for _id in data['league_id'].unique():
    segment = data[(data['league_id'] == _id)]
    
    # COVID case, no games in a year. If there is no attendance, return a dataframe with 0 attendance and 0 probability density.
    if segment['attendance'].min() == 0 and segment['attendance'].max() == 0:
        x = [0]
        y = [1]
    else:
      x = np.linspace(start=segment['attendance'].min(),
            stop=segment['attendance'].max(),
            num=200) 
      pdf = scipy.stats.gaussian_kde(segment['attendance'])
      y = pdf.evaluate(x)
      y /= sum(y)  # Normalize the KDE to 1

    kdes.append(pd.DataFrame({
            'attendance': x,
            'probability_density': y,
            'league_id': _id,
        })  )
    
  kdes = pd.concat(kdes, ignore_index=True)
  kdes['attendance_league_id'] = kdes['league_id'].astype(str) + "-" + kdes['attendance'].astype(str)
      
  return kdes
  
def violins(kdes, season):
    league_segment = kdes[kdes['league_id'] == league_id]
  
    min_a = league_segment['attendance'].min() - 0.05*league_segment['attendance'].max()
    max_a = 1.05*league_segment['attendance'].max()
    
    plots = []
    for tier in league_segment['league_tier'].unique():
      segment = league_segment[league_segment['league_tier'] == tier]
      plot = figure(
          title=f"Attendance distribution per season for tier {tier} and season {season}",
          x_axis_label="Attendance",
          y_axis_label="Density",
          #sizing_mode='stretch_width',
          width=500,
          height=200,
          x_range=(min_a, max_a)
          )
      plot.varea(
          x=segment['attendance'],
          y1=segment['probability_density'],
          y2=0,
          fill_color='blue',
          fill_alpha=0.5
      )
      plot.yaxis.visible = False
      plot.ygrid.visible = False
      
      plots.append(plot)
    
    return plots
    

# %%---------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    connection_params = {
        'host': "localhost",
        'port': 5433,
        'database': "Football",
        'user': "postgres",
        'password': "snowman1517"
    }
    data = attendance(connection_params)
    kdes = get_kdes(data)
    
    kdes.to_csv('Attendance_violin/Data/attendance_violin.csv', index=False)
    
    # Demo plot
  #  season = 2024
  #  plots = column(violins(kdes, season))
  #  show(plots)
