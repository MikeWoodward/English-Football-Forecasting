#!/usr/bin/env python3
"""
Script to scrape historical football match data from enfa.co.uk.

This script uses Selenium to navigate to enfa.co.uk, access the matches section,
and download match data for September 1888.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import NoReturn

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from random import randint

# Configure logging
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

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.

    Raises:
        WebDriverException: If there's an error setting up the WebDriver.
    """
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Set a standard Chrome user agent
        user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/137.0.0.0 Safari/537.36'
        )
        options.add_argument(f'user-agent={user_agent}')
        # Use webdriver-manager to get the correct ChromeDriver
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {str(e)}")
        raise


def setup_page() -> webdriver.Chrome | None:
    """
    Set up the initial page state and navigate to the matches section.

    Returns:
        webdriver.Chrome | None: Configured WebDriver instance or None if setup fails.
    """
    driver = None
    try:
        driver = setup_driver()
        driver.get("https://enfa.co.uk")

        # Random pause to be kind to the server
        time.sleep(randint(2,10))
        
        # Switch to menu iframe
        driver.switch_to.frame(2)

        # Click on Matches in the left menu
        matches_link = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Matches"))
        )
        matches_link.click()
        
        # Switch to main iframe
        driver.switch_to.parent_frame()
        driver.switch_to.frame(3)

        # Wait for dates table to draw
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CLASS_NAME, 'header'))
        )
    except WebDriverException as e:
        logger.error(f"WebDriver error: {str(e)}")
    return driver


def scrape_matches(driver: webdriver.Chrome, year: str, month: str) -> None:
    """
    Scrape all available match data for September 1888 from enfa.co.uk.

    The function navigates to the website, clicks through to September 1888,
    and saves match data for each available date.
    """
    try:
        # Random pause to be kind to the server
        time.sleep(randint(2,10))

        # Select month from month dropdown
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
        time.sleep(randint(2,10))

        # Select year from year dropdown
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
        time.sleep(randint(5,10))

        # Now get the table
        table = (
            WebDriverWait(driver, 20)
            .until(EC.visibility_of_element_located((By.CLASS_NAME, 'header')))
            .get_attribute("outerHTML")
        )

        # Find all the active days
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
        time.sleep(randint(5,10))

        # Click on each active day in turn
        if days:
            for day in days:

                # Get the date string we expect in the table
                date_str = f"{year}-{month}-{day}"
                expected_date = datetime.strptime(date_str, "%Y-%B-%d")
                expected_date_str = expected_date.strftime("%A, %B %d, %Y")

                logger.info(f"Processing day {expected_date}")

                # Check if the HTML has already been downloaded, if it has, skip it
                html_file_name = os.path.join("HTML", f"{expected_date.strftime('%Y-%m-%d')}.html")
                if os.path.exists(html_file_name):
                    continue

                # Click on the day
                matches_link = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, day))
                )
                matches_link.click()

                # Random pause to be kind to the server
                time.sleep(randint(5,10))

                # Wait for the table to be present
                WebDriverWait(driver, 20).until(
                    EC.text_to_be_present_in_element(
                        (By.XPATH, "//table[2]"), 
                        expected_date_str
                    )
                )

                tables = driver.find_elements(By.TAG_NAME, "table")

                # Extract wanted HTML
                html_content = ""
                for table in tables[2:]:
                    html_content += table.get_attribute("outerHTML")
                    html_content += "<hr>"
                
                # If there's HTML, save it to a file with a name based on date
                if html_content:
                    # Prepend the day and date to the HTML
                    header = (
                        f"{expected_date.strftime('%A')}<br>"
                        f"{expected_date.strftime('%Y-%m-%d')}<hr>"
                    )
                    html_content = header + html_content
                    
                    # Save to the location "HTML"
                    with open(html_file_name, "w") as f:
                        f.write(html_content)

    except WebDriverException as e:
        logger.error(f"WebDriver error: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    years = [str(year) for year in range(1888, 2025)]
    try:
        for year in years:
            for month in months:
                driver = setup_page()
                scrape_matches(driver, year, month)
                driver.quit()
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        raise 