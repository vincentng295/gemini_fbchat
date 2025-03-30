from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import sys
import json
import random
from urllib.parse import urlparse
from fbparser import get_facebook_profile_url
import re
from js_selenium import inject_my_stealth_script, get_profile_switcher_ids
from datetime import datetime

def hide_email(email):
    match = re.match(r'(\w+)@(\w+)\.(\w+)', email)
    if match:
        return f"{match.group(1)[0]}***@***.{match.group(3)[0]}***"
    return email  # Return original if it doesn't match

cwd = os.getcwd()

import pyotp
def generate_otp(secret_key):
    totp = pyotp.TOTP(secret_key.replace(" ",""))
    return totp.now()

def wait_until_safe_totp_time():
    while True: 
        second = datetime.now().second
        if 0 <= second <= 20 or 30 <= second <= 50:
            return True
        time.sleep(1)

def is_facebook_domain(url):
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc.lower()
    return netloc == "facebook.com" or netloc.endswith(".facebook.com")

def get_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path.rstrip("/")

def base_url_with_path(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc + parsed_url.path.rstrip("/")

def human_typing(element, text):
    for char in text:
        element.send_keys(char)
        # Random delay to emulate human typing speed
        time.sleep(random.uniform(0.1, 0.25))  # Between 100ms to 250ms

def parse_cookies(cookies_text):
    """
    Parse a cookies string in the format "name1=value1; name2=value2; ..."
    and return a list of dictionaries suitable for `add_cookie`.
    """
    cookies = []
    for cookie_pair in cookies_text.split(';'):
        cookie_pair = cookie_pair.strip()
        if not cookie_pair or '=' not in cookie_pair:
            continue  # skip empty or malformed pairs
        name, value = cookie_pair.split('=', 1)
        cookies.append({
            'name': name.strip(),
            'value': value.strip(),
            'domain': '.facebook.com',
            'httpOnly': False,
            'path': '/',
            'sameSite': 'Lax',
            'secure': False
        })
    return cookies

def sanitize_cookie_value(value):
    # Basic sanitization to remove semicolons and newlines (both invalid in cookie headers)
    return value.replace(';', '%3B').replace('\n', '')

def selenium_cookies_to_cookie_header(cookies):
    return '; '.join(
        f"{cookie['name']}={sanitize_cookie_value(cookie['value'])}"
        for cookie in cookies
    )

def __chrome_driver__(scoped_dir = None, headless = True, incognito = False):
    # Set up Chrome options
    chrome_options = Options()
    # Block popups and notifications
    prefs = {
        "profile.default_content_setting_values.popups": 2,
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    # Enable headless mode if requested
    if headless:
        chrome_options.add_argument("--headless=new")
    if incognito:
        chrome_options.add_argument("--incognito")
    # Set window size and disable GPU for consistency
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    # Stealth options to mask automation
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("disable-infobars")
    # Other useful options
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=en-US")
    # (Optional) Set a common user agent string
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                 "AppleWebKit/537.36 (KHTML, like Gecko) " \
                 "Chrome/105.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    # Use a specific user data directory if provided
    if scoped_dir:
        chrome_options.add_argument(f"--user-data-dir={scoped_dir}")
        
    # Define the path to the directory containing unpacked extension directories
    extensions_dir = f"{cwd}/setup/plugins"

    # Iterate through every directory under the path and add as an unpacked extension
    for dir_name in os.listdir(extensions_dir):
        extension_path = os.path.join(extensions_dir, dir_name)
        if os.path.isdir(extension_path):  # Check if it's a directory
            chrome_options.add_argument(f"--load-extension={extension_path}")

    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    # Load a blank page and further modify navigator properties to mask automation flags
    driver.get("data:text/html,<html><head></head><body></body></html>")
    inject_my_stealth_script(driver)
    return driver

def get_facebook_id_from_cookies(cookies):
    c_user, i_user = get_facebook_all_id_from_cookies(cookies)
    return i_user if i_user is not None else c_user

def get_facebook_all_id_from_cookies(cookies):
    if not cookies:
        return None, None
    c_user, i_user = None, None
    for cookie in cookies:
        if cookie.get("name", "") == "i_user":
            i_user = cookie.get("value", None)
        if cookie.get("name", "") == "c_user":
            c_user = cookie.get("value", None)
    return c_user, i_user

def set_facebook_id(driver, c_user, i_user = None):
    if c_user is None:
        return
    driver.add_cookie({
            'name': "c_user",
            'value': c_user,
            'domain': '.facebook.com',
            'httpOnly': False,
            'path': '/',
            'sameSite': 'Lax',
            'secure': False
        })
    if i_user is not None:
        driver.add_cookie({
                'name': "i_user",
                'value': i_user,
                'domain': '.facebook.com',
                'httpOnly': False,
                'path': '/',
                'sameSite': 'Lax',
                'secure': False
            })
    else:
        driver.delete_cookie("i_user")

def is_facebook_logged_out(cookies):
    for cookie in cookies:
        if cookie.get("name", "") == "xs":
            return (cookie.get("value", None) is None)
    return True

def delete_cookie(cookies, name):
    # Remove any existing cookie with the same name
    cookies = [c for c in cookies if c.get("name") != name]

def add_cookie(cookies, cookie):
    """
    Add or update a cookie in the cookies list.
    Parameters:
    - cookies (list of dict): List of cookie dictionaries.
    - cookie (dict): A single cookie dictionary to add or update.
    Returns:
    - list of dict: Updated list of cookies.
    """
    name = cookie.get("name")
    if not name:
        raise ValueError("Cookie must have a 'name' field")
    # Remove any existing cookie with the same name
    delete_cookie(cookies, name)
    # Append the new cookie
    cookies.append(cookie)

def check_cookies_(cookies):
    if cookies == None:
        return 0
    try:
        current_url = get_facebook_profile_url(cookies)
        if not is_facebook_domain(current_url):
            return 0
        path = get_path(current_url)
        if not path or path == "www.facebook.com/login":
            return 0
        if path.startswith("/checkpoint/"):
            return -1
        print("Đăng nhập thành công:", current_url)
    except Exception as e:
        print(f"Error: {e}")
        return 0
    return 1

def check_cookies(filename=None):
    try:
        cookies = None
        if filename:
            with open(filename, "r", encoding='utf-8') as f:
                cookies = json.load(f)
        return check_cookies_(cookies), cookies
    except Exception as e:
        print(f"Error loading cookies from file: {e}")
        return 0, cookies

def get_fb_cookies(username, password, otp_secret = None, alt_account = 0, cookies = None, incognito = False, finally_stop = False):
    if password is None or password == "":
        return 0, None
    try:
        scoped_dir = os.getenv("SCPDIR")
        driver = __chrome_driver__(scoped_dir, False, incognito)

        actions = ActionChains(driver)
        
        wait = WebDriverWait(driver, 20)

        def find_element_when_clickable(by, selector):
            return wait.until(EC.element_to_be_clickable((by, selector)))
        
        def find_element_when_clickable_in_list(elemlist):
            for btn_select in elemlist:
                try:
                    return find_element_when_clickable(btn_select[0], btn_select[1])
                    break
                except Exception:
                    continue
            return None

        driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": True})
        driver.get("https://www.facebook.com")
        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        if type(cookies) == list:
            wait.until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            driver.delete_all_cookies()
            for cookie in cookies:
                cookie.pop('expiry', None)  # Remove 'expiry' field if it exists
                driver.add_cookie(cookie)
            print("Đã khôi phục cookies")

        driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": False})
        driver.get("https://www.facebook.com")
        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(0.5)

        prelogin = driver.find_elements(By.CSS_SELECTOR, 'a[href="#"][data-onclick]')
        if len(prelogin) > 0:
            actions.move_to_element(prelogin[0]).click().perform()
        else:
            form = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'form[action^="/login/"]')))
            email_input = find_element_when_clickable(By.NAME, "email")
            password_input = find_element_when_clickable(By.NAME, "pass")
            actions.move_to_element(email_input).click().perform()
            time.sleep(random.randint(5,10))
            human_typing(email_input, username)
            actions.move_to_element(password_input).click().perform()
            time.sleep(random.randint(5,10))
            human_typing(password_input, password)
            
            time.sleep(random.randint(5,10))
            button = find_element_when_clickable_in_list([
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'button[id="loginbutton"]'),
            ])
            form = button.find_element(By.XPATH, "./ancestor::form")
            # inject to save login
            driver.execute_script("""
                var form = arguments[0];
                var input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'savepass';
                input.value = '';
                form.appendChild(input);
            """, form)
            actions.move_to_element(button).click().perform()
            print(f"{hide_email(username)}: Đang đăng nhập...")
        time.sleep(1)
        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        _url = base_url_with_path(driver.current_url)
        print(_url)
        if  (_url == "www.facebook.com"):
            print(f"{hide_email(username)}: Đang chờ Facebook xác thực đăng nhập...")
            for i in range(300):
                _url = base_url_with_path(driver.current_url)
                if  (_url == "www.facebook.com"):
                    time.sleep(1)
                else:
                    break
        print(_url)
        _url = base_url_with_path(driver.current_url)
        if  (_url == "www.facebook.com/two_step_verification/two_factor"):
            try:
                print(f"{hide_email(username)}: Chưa phê duyệt đang nhập. Đang tiến hành Xác minh đăng nhập 2 bước tự động với OTP")
                otp_input_type = driver.find_elements(By.CSS_SELECTOR, 'input[type="text"]')
                if len(otp_input_type) == 0:
                    other_veri_btn = find_element_when_clickable_in_list([
                        (By.XPATH, '//span[contains(text(), "Thử cách khác")]'),
                        (By.XPATH, '//span[contains(text(), "Try another way")]')
                        ])
                    time.sleep(1)
                    print(f"{hide_email(username)}: Nhấn thay đổi phương thức xác thực")
                    other_veri_btn.click() # Click other verification method
                    #time.sleep(random.randint(1,3))
                    other_veri_btn = find_element_when_clickable_in_list([
                        (By.XPATH, '//div[contains(text(), "Ứng dụng xác thực")]'),
                        (By.XPATH, '//div[contains(text(), "Authentication app")]')
                        ])
                    time.sleep(1)
                    print(f"{hide_email(username)}: Chọn xác thực bằng mã OTP từ ứng dụng xác thực")
                    other_veri_btn.click() # Click App Auth method
                    other_veri_btn = find_element_when_clickable_in_list([
                        (By.XPATH, '//span[contains(text(), "Tiếp tục")]'),
                        (By.XPATH, '//span[contains(text(), "Continue")]')
                        ])
                    time.sleep(1)
                    print(f"{hide_email(username)}: Nhấn vào nút Tiếp tục")
                    other_veri_btn.click() # Click Continue
                other_veri_btn = find_element_when_clickable(By.CSS_SELECTOR, 'input[type="text"]')
                continue_btn = find_element_when_clickable_in_list([
                    (By.XPATH, '//span[contains(text(), "Tiếp tục")]'),
                    (By.XPATH, '//span[contains(text(), "Continue")]')
                    ])
                time.sleep(1)
                wait_until_safe_totp_time()
                print(f"{hide_email(username)}: Đã nhập mã OTP")
                other_veri_btn.send_keys(generate_otp(otp_secret) + "\n")
                time.sleep(1)
                print(f"{hide_email(username)}: Nhấn xác nhận")
                continue_btn.click() # Click Confirmed
            except Exception as e:
                print(f"Error: {e}")

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        _url = base_url_with_path(driver.current_url)
        print(_url)
        if  (_url == "www.facebook.com/two_step_verification/two_factor" or 
            _url.startswith("www.facebook.com/auth_platform/")):
            print(f"{hide_email(username)}: Đang chờ Facebook xác thực. Nếu đã đăng nhập tài khoản này từ thiết bị khác, bạn có thể phê duyệt từ thiết bị đó khác trong vòng 60 giây...")
            for i in range(60):
                _url = base_url_with_path(driver.current_url)
                if  (_url == "www.facebook.com/two_step_verification/two_factor" or 
                    _url.startswith("www.facebook.com/auth_platform/")):
                    time.sleep(1)
                else:
                    break

        _url = base_url_with_path(driver.current_url)
        print(_url)
        if _url.startswith("www.facebook.com/checkpoint/"):
            print(f"Tài khoản dính checkpoint [{_url}]")
            return -1, None

        driver.get("https://www.facebook.com/profile.php")

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(3)

        c_user, i_user = get_facebook_all_id_from_cookies(driver.get_cookies())
        if isinstance(alt_account, int) and alt_account > 0:
            ids = get_profile_switcher_ids(driver)
            if alt_account <= len(ids):
                set_facebook_id(driver, c_user, ids[alt_account -1])
                print(f"Đã chuyển sang: {ids[alt_account -1]}")

        driver.get("https://www.facebook.com/profile.php")

        wait.until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(3)

        if finally_stop:
            input("<< Nhấn Enter để tiếp tục >>")
        cookies = driver.get_cookies()
        _url = base_url_with_path(driver.current_url)
        if _url == "www.facebook.com" or _url == "www.facebook.com/login":
            print(f"Đăng nhập thất bại [{_url}]")
            return 0, None
        print(f"{hide_email(username)}: Đăng nhập thành công [{driver.current_url}]")
    except Exception as e:
        print(f"Error: {e}")
        return 0, None
    finally:
        driver.quit()
        
    return 1, cookies

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    # Use disabled Facebook account for testing :>
    result, _ = get_fb_cookies(
        "cthigiang952@mailpro.live", 
        "CaoGiang$0900", 
        "2526 VJOL P2TH UXNZ RAXD G3V5 I4DX AIFF"
    )
    if result != 0:
        print("Kiểm tra thành công")
    else:
        raise Exception("Test unsuccessful!")
