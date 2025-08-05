#!/usr/bin/env python3
"""
Script to scrape historical football match data from enfa.co.uk.

This script uses Selenium to navigate to enfa.co.uk, access the matches section,
and download match data from September 1888.
"""

import logging
import os
import time
from datetime import datetime
from typing import NoReturn

from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from random import randint

# Configure logging to capture both file and console output
# This ensures we have a complete record of the scraping process
log_file = os.path.join("Logs", "0_enfa_matches.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_driver() -> webdriver.Chrome:
    """
    Set up and return a configured Chrome WebDriver instance.

    This function configures Chrome WebDriver with appropriate options for web
    scraping, including user agent settings and security options to avoid
    detection.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.

    Raises:
        WebDriverException: If there's an error setting up the WebDriver.
    """
    try:
        # Configure Chrome options for web scraping
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Set a standard Chrome user agent to avoid detection
        user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/137.0.0.0 Safari/537.36'
        )
        options.add_argument(f'user-agent={user_agent}')

        # Use webdriver-manager to automatically get the correct ChromeDriver
        # version
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise


def setup_page() -> webdriver.Chrome | None:
    """
    Set up the initial page state and navigate to the matches section.

    This function navigates to enfa.co.uk, handles the iframe structure,
    and positions the browser at the matches section ready for data extraction.

    Returns:
        webdriver.Chrome | None: Configured WebDriver instance or None if
        setup fails.
    """
    driver = None
    try:
        # Initialize the WebDriver
        driver = setup_driver()
        driver.get("https://enfa.co.uk")

        # Random pause to be kind to the server and avoid rate limiting
        time.sleep(randint(2, 10))

        # Switch to menu iframe (iframe index 2 contains the navigation menu)
        driver.switch_to.frame(2)

        # Click on Matches in the left menu to access match data
        matches_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Matches"))
        )
        matches_link.click()

        # Switch to main iframe (iframe index 3 contains the main content area)
        driver.switch_to.parent_frame()
        driver.switch_to.frame(3)

        # Wait for dates table to load and become visible
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'header'))
        )
    except WebDriverException as e:
        logger.error(f"WebDriver error: {str(e)}")
    return driver


def scrape_matches(driver: webdriver.Chrome, year: str, month: str) -> None:
    """
    Scrape all available match data for a specific year and month from
    enfa.co.uk.

    This function navigates through the website's date selection interface,
    extracts available match dates, and downloads HTML content for each date
    that contains match data.

    Args:
        driver: WebDriver instance positioned at the matches page
        year: Year to scrape (e.g., "1888")
        month: Month to scrape (e.g., "September")

    Raises:
        WebDriverException: If there are issues with web navigation or element
        interaction
    """
    try:
        # Random pause to be kind to the server
        time.sleep(randint(2, 10))

        # Select month from month dropdown menu
        month_dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.NAME, "month"))
        )
        month_dropdown.click()
        month_option = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//option[text()='{month}']")
            )
        )
        month_option.click()

        # Random pause to be kind to the server
        time.sleep(randint(2, 10))

        # Select year from year dropdown menu
        year_dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.NAME, "year"))
        )
        year_dropdown.click()
        year_option = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//option[text()='{year}']")
            )
        )
        year_option.click()

        # Random pause to be kind to the server
        time.sleep(randint(5, 10))

        # Extract the HTML table containing the date selection interface
        table = (
            WebDriverWait(driver, 20)
            .until(EC.visibility_of_element_located((By.CLASS_NAME, 'header')))
            .get_attribute("outerHTML")
        )

        # Parse the HTML to find all active days (days with match data)
        # The website uses JavaScript functions like displayMatch(day) to
        # indicate active dates
        days = []
        while True:
            start_index = table.find("displayMatch(")
            if start_index == -1:
                break
            length = table[start_index:].find(")")
            if length == -1:
                break
            day = table[start_index + 13:start_index + length]
            days.append(day)
            table = table[start_index + length:]

        # Random pause to be kind to the server
        time.sleep(randint(5, 10))

        # Click on each active day in turn to extract match data
        if days:
            for day in days:

                # Get the date string we expect in the table
                date_str = f"{year}-{month}-{day}"
                expected_date = datetime.strptime(date_str, "%Y-%B-%d")
                expected_date_str = expected_date.strftime("%A, %B %d, %Y")

                logger.info(f"Processing day {expected_date}")

                # Check if the HTML has already been downloaded, if it has, skip
                # it
                # This prevents re-downloading data and speeds up the process
                html_file_name = os.path.join(
                    "HTML", f"{expected_date.strftime('%Y-%m-%d')}.html"
                )
                if os.path.exists(html_file_name):
                    continue

                # Click on the day to load the match data
                matches_link = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, day))
                )
                matches_link.click()

                # Random pause to be kind to the server
                time.sleep(randint(5, 10))

                # Wait for the table to be present and contain the expected date
                WebDriverWait(driver, 20).until(
                    EC.text_to_be_present_in_element(
                        (By.XPATH, "//table[2]"),
                        expected_date_str
                    )
                )

                # Extract all tables from the page (match data is in tables 2
                # onwards)
                tables = driver.find_elements(By.TAG_NAME, "table")

                # Extract wanted HTML content from all match tables
                html_content = ""
                for table in tables[2:]:
                    html_content += table.get_attribute("outerHTML")
                    html_content += "<hr>"

                # If there's HTML content, save it to a file with a name based
                # on date
                if html_content:
                    # Prepend the day and date to the HTML for context
                    header = (
                        f"{expected_date.strftime('%A')}<br>"
                        f"{expected_date.strftime('%Y-%m-%d')}<hr>"
                    )
                    html_content = header + html_content

                    # Save to the HTML directory with date-based filename
                    with open(html_file_name, "w") as f:
                        f.write(html_content)

    except WebDriverException as e:
        logger.error(f"WebDriver error: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Define the months and years to scrape
    # This covers the entire history from 1888 to present day
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    years = [str(year) for year in range(1888, 2025)]

    try:
        # Iterate through all years and months to scrape complete dataset
        for year in years:
            for month in months:
                # Set up the page for each year/month combination
                driver = setup_page()
                # Scrape matches for the current year/month
                scrape_matches(driver, year, month)
                # Clean up the driver
                driver.quit()
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise 