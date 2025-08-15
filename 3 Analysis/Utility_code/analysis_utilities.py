"""
Analysis utilities module for EPL predictor project.

This module contains utility functions and classes for data analysis tasks.
"""

import os
import webbrowser
from typing import List
import bokeh


def save_plots(
    *,
    divs: List[str],
    scripts: List[str],
    titles: List[str],
    file_name: str
) -> None:
    """
    Save the plots to the HTML folder.

    This function creates an HTML file containing Bokeh plots with interactive
    functionality. It also saves individual script and div files for debugging
    and reference purposes.

    Args:
        divs: List of HTML div strings containing plot elements.
        scripts: List of JavaScript script strings for plot interactivity.
        titles: List of plot titles corresponding to divs and scripts.
        file_name: Name of the output HTML file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the Plots directory doesn't exist.
        OSError: If there are issues writing to files.
    """
    # Define the output directory for all plot-related files
    folder_name = "Plots"

    # Create the Plots directory if it doesn't exist
    # This ensures the directory structure is available before writing files
    os.makedirs(folder_name, exist_ok=True)

    # Get Bokeh version for proper script imports
    # This ensures compatibility with the specific Bokeh version being used
    version = bokeh.__version__

    # Construct the CDN script imports for Bokeh libraries
    # These scripts provide the necessary JavaScript functionality for plots
    imported_scripts = (
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-widgets-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-tables-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-mathjax-{version}.min.js"></script>\n"""
    )

    # Sample text content for the HTML page
    # This provides placeholder content between plots for better presentation
    lorem = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        "eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim "
        "ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum."
    )

    # Create HTML file with the generated plot
    # This is the main output file that will be opened in the browser
    try:
        with open(os.path.join(folder_name, file_name), "w") as f:
            # Header equivalent - include Bokeh script imports
            # These scripts must be loaded before any plot content
            f.write("<!-- Script imports -->\n")
            f.write(imported_scripts)

            # Body equivalent - add HTML content
            # Start the main content section of the HTML document
            f.write("<!-- HTML body -->\n")

            # Add introductory text content
            f.write(f"""<p>{lorem}</p>\n""")

            # Iterate through each plot div and add it to the HTML
            # Each plot is wrapped in a centered div for proper alignment
            for index, div in enumerate(divs):
                # Plot container with center alignment
                # This ensures plots are visually centered on the page
                f.write(f"<!-- Plot {titles[index]} -->\n")
                f.write("<div align='center'>\n")
                f.write(div)
                f.write("\n")
                f.write("</div>\n")

                # Add separator text between plots for better readability
                f.write(f"""<p>{lorem}</p>\n""")

            # Chart scripts for interactive functionality
            # These scripts enable plot interactivity and must be placed after divs
            f.write("<!-- Chart scripts -->\n")
            for index, script in enumerate(scripts):
                f.write(f"<!-- Plot {titles[index]} -->\n")
                f.write(script)
                f.write("\n")
    except FileNotFoundError as e:
        # Handle case where directory creation failed or path is invalid
        print(f"Error on line {e.__traceback__.tb_lineno}: Plots directory not "
              f"found. Line content: 'with open(os.path.join(\"{folder_name}\", "
              f"\"file_name\"), \"w\") as f:'")
        raise
    except OSError as e:
        # Handle general file system errors (permissions, disk full, etc.)
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"HTML file. Line content: 'with open(os.path.join(\"Plots\", "
              f"\"file_name\"), \"w\") as f:'")
        raise

    # Write each of the scripts to a separate file
    # This allows for individual debugging and inspection of plot scripts
    try:
        for index, script in enumerate(scripts):
            # Create individual script files with descriptive names
            script_filename = f"script_{index+1}.txt"
            with open(os.path.join("Plots", script_filename), "w") as f:
                f.write(f"<!--Chart script {titles[index]}-->\n")
                f.write(script)
    except OSError as e:
        # Handle errors when writing individual script files
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"script files. Line content: 'with open(os.path.join(\"Plots\", "
              f"f\"script_{index+1}.txt\"), \"w\") as f:'")
        raise

    # Write all scripts to a combo file
    # This creates a single file containing all scripts for easy reference
    try:
        with open(os.path.join(folder_name, "scripts.txt"), "w") as f:
            f.write(f"<!-- {file_name} scripts -->\n")
            f.write("<!------------------------>\n")

            # Add each script with its corresponding title
            for index, script in enumerate(scripts):
                f.write(f"<!--Chart script {titles[index]}-->\n")
                f.write(script)
                f.write("\n")
    except OSError as e:
        # Handle errors when writing the combined scripts file
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"scripts combo file. Line content: 'with open(os.path.join("
              f"\"{folder_name}\", \"scripts.txt\"), \"w\") as f:'")
        raise

    # Write each of the divs to a separate file
    # This allows for individual inspection and debugging of plot HTML
    try:
        for index, div in enumerate(divs):
            # Create individual div files with descriptive names
            div_filename = f"div_{index+1}.txt"
            with open(os.path.join(folder_name, div_filename), "w") as f:
                f.write(f"<!-- Plot {titles[index]} -->\n")
                f.write("<div align='center'>\n")
                f.write("    " + div)  # Indent the div content for readability
                f.write("\n")
                f.write("</div>\n")
    except OSError as e:
        # Handle errors when writing individual div files
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"div files. Line content: 'with open(os.path.join(\"{folder_name}\", "
              f"f\"div_{index+1}.txt\"), \"w\") as f:'")
        raise

    # Open the generated plot in the default web browser
    # This provides immediate visual feedback of the generated plots
    try:
        # Construct the full file path and convert to file:// URL format
        file_path = os.path.abspath(os.path.join(folder_name, file_name))
        file_url = 'file:///' + file_path
        webbrowser.open(file_url)
    except Exception as e:
        # Handle any errors that might occur when opening the browser
        # This includes browser not found, file not accessible, etc.
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to open "
              f"browser. Line content: 'webbrowser.open('file:///' + "
              f"os.path.abspath(os.path.join(\"{folder_name}\", "
              f"\"{file_name}\")))'")
        raise

