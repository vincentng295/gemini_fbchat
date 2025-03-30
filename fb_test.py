from fb_getcookies import __chrome_driver__
from selenium import webdriver
import json
import time
import os

# Path to your cookies.json file
cookies_file_path = 'cookies.json'

# Initialize the WebDriver (you may need to adjust this depending on the browser and its version)
driver = __chrome_driver__(headless=False)
try:
    # Open Facebook
    driver.get("https://www.facebook.com")

    # Check if the cookies.json file exists
    if os.path.exists(cookies_file_path):
        # Load cookies from the JSON file
        with open(cookies_file_path, 'r') as file:
            cookies = json.load(file)

        # Add each cookie to the browser
        for cookie in cookies:
            # Make sure the cookie is not missing any essential field
            if 'name' in cookie and 'value' in cookie:
                driver.add_cookie(cookie)

        # Reload the page to apply cookies
        driver.refresh()

        # Wait a few seconds to ensure the page reloads and the cookies are applied
        time.sleep(5)

    else:
        print("cookies.json not found. Skipping cookie restoration.")

    # Wait for the user to press Enter before extracting and saving the cookies
    input("Press Enter to extract cookies and save them...")

    # Extract cookies from the browser and save them to the file
    current_cookies = driver.get_cookies()

    # Save the cookies back to the JSON file
    with open(cookies_file_path, 'w') as file:
        json.dump(current_cookies, file)

    print("Cookies saved successfully!")
finally:
    # Detach the driver (you can close it if needed)
    driver.quit()
