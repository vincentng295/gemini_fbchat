import sys
from fb_getcookies import __chrome_driver__, parse_cookies, get_facebook_all_id_from_cookies
from selenium import webdriver
import json
import time
import os
from js_selenium import get_profile_switcher_ids

if __name__ == "__main__":
    cookies_file_path = 'cookies.json'

    # Check if the script is run with --import <path_to_raw_cookies>
    if len(sys.argv) == 3 and sys.argv[1] == "--import":
        raw_cookie_path = sys.argv[2]
        parsed_cookies = parse_cookies(raw_cookie_path)
        with open(cookies_file_path, 'w') as f:
            json.dump(parsed_cookies, f)
        print(f"Cookies imported and saved to {cookies_file_path}")

    # Otherwise, proceed with loading cookies in the browser
    driver = __chrome_driver__(headless=False)
    try:
        driver.get("https://www.facebook.com")

        if os.path.exists(cookies_file_path):
            with open(cookies_file_path, 'r') as file:
                cookies = json.load(file)

            for cookie in cookies:
                if 'name' in cookie and 'value' in cookie:
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Failed to add cookie: {cookie.get('name')} - {e}")

            driver.refresh()
            time.sleep(5)
        else:
            print("cookies.json not found. Skipping cookie restoration.")

        input("Press Enter to extract cookies and save them...")

        current_cookies = driver.get_cookies()
        with open(cookies_file_path, 'w') as file:
            json.dump(current_cookies, file)
        c_user, i_user = get_facebook_all_id_from_cookies(current_cookies)
        print(f"ID: {c_user}, second ID: {i_user}")
        print("Eligible Profile IDs:", get_profile_switcher_ids(driver))
        print("Cookies saved successfully!")
    finally:
        driver.quit()