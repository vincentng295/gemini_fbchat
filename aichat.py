import os  # For environment variable handling
import json  # For handling JSON data
import time  # For time-related functions
import sys  # For system-specific parameters and functions
import copy # For deepcopy
from datetime import datetime  # For date and time manipulation
import pytz  # For timezone handling
from io import BytesIO  # For handling byte streams
import requests  # For making HTTP requests
from urllib.parse import urljoin, urlparse  # For URL manipulation
from hashlib import md5  # For hashing
import re
import shutil
from selenium import webdriver  # For web automation
from selenium.webdriver.common.by import By  # For locating elements
from selenium.webdriver.chrome.service import Service  # For Chrome service
from selenium.webdriver.common.action_chains import ActionChains  # For simulating user actions
from selenium.webdriver.support.ui import WebDriverWait  # For waiting for elements
from selenium.webdriver.support import expected_conditions as EC  # For expected conditions
from selenium.common.exceptions import *  # For handling exceptions
from selenium.webdriver.common.keys import Keys  # For keyboard actions
from selenium.common.exceptions import *
import google.generativeai as genai  # For generative AI functionalities
from pickle_utils import *  # For pickling data
from github_utils import *  # For GitHub file operations
from fbparser import get_facebook_profile_url, get_facebook_id
from fb_getcookies import __chrome_driver__ 
from fb_getcookies import * # For Facebook cookie handling
from aichat_utils import *  # For custom utility functions
from js_selenium import js_pushstate, inject_my_stealth_script

def get_day_and_time():
    # Get current date and time
    current_datetime = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
    # Format the output
    return current_datetime.strftime("%A, %d %B %Y - %H:%M:%S")

def print_with_time(*args, sep=" ", end="\n", file=None, flush=False): 
    print(get_day_and_time(), ":", *args, sep=sep, end=end, file=file, flush=flush)

sys.stdout.reconfigure(encoding='utf-8')

genai_key = os.getenv("GENKEY", None)
scoped_dir = os.getenv("SCPDIR")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "") # Pass GitHub Token
GITHUB_REPO = os.getenv("GITHUB_REPO")   # Pass the repository (owner/repo)
STORAGE_BRANCE = os.getenv("STORAGE_BRANCE")
PASSWORD = os.getenv("PASSWORD", "")

# Generate key for encrypt and decrypt
encrypt_key = generate_fernet_key(PASSWORD)

# cookies filename
filename = "cookies.json"
bakfilename = "cookies_bak.json"

on_github_workflows = (GITHUB_TOKEN is not None and GITHUB_TOKEN != "")
headless = os.getenv("HEADLESS", "false").lower() == "true"

f_intro_txt = "setup/introduction.txt"
f_rules_txt = "setup/rules.txt"

with open(f_intro_txt, "r", encoding='utf-8') as f: # What kind of person will AI simulate?
    ai_prompt = f.read()

cwd = os.getcwd()
print_with_time(cwd)

driver = None

def update():
    pass

try:
    # Initialize the driver
    driver = __chrome_driver__(scoped_dir, headless)
    actions = ActionChains(driver)

    tz_params = {'timezoneId': 'Asia/Ho_Chi_Minh'}
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)
    add_block_fb_images(driver)
    chat_tab = driver.current_window_handle

    driver.switch_to.new_window('tab')
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)
    switch_to_mobile_view(driver)
    inject_my_stealth_script(driver)
    mobileview = driver.current_window_handle
    
    driver.switch_to.window(chat_tab)
    
    wait = WebDriverWait(driver, 10)
    
    print_with_time("Đang tải dữ liệu từ cookies")
    
    try:
        with open(filename, "r", encoding='utf-8') as f:
            cookies = json.load(f)
    except Exception:
        cookies = []    
    try:
        with open("cookies_bak.json", "r", encoding='utf-8') as f:
            bak_cookies = json.load(f)
    except Exception:
        bak_cookies = None

    try:
        with open("logininfo.json", "r", encoding='utf-8') as f:
            login_info = json.load(f)
            onetimecode = login_info.get("onetimecode", "")
            work_jobs = parse_opts_string(login_info.get("work_jobs", "aichat,friends"))
    except Exception as e:
        onetimecode = ""
        work_jobs = parse_opts_string("aichat,friends")
        print_with_time(e)

    print_with_time("Danh sách jobs:", work_jobs)

    # global regex
    global_reset_regex = work_jobs.get("aichat_resetat", None)
    global_reset_msg = work_jobs.get("aichat_resetmsg", None)
    global_stop_regex = work_jobs.get("aichat_stopat", None)
    global_stop_msg = work_jobs.get("aichat_stopmsg", None)
    global_start_regex = work_jobs.get("aichat_startat", None)
    global_start_msg = work_jobs.get("aichat_startmsg", None)
    global_bye_msg = work_jobs.get("aichat_byemsg", None)
    admin_fbid = work_jobs.get("aichat_adminfbid", "100013487195619")

    driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": True})
    driver.get("https://www.facebook.com/")
    driver.delete_all_cookies()
    for cookie in cookies:
        cookie.pop('expiry', None)  # Remove 'expiry' field if it exists
        driver.add_cookie(cookie)
    print_with_time("Đã khôi phục cookies")
    driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": False})
    driver.get("https://www.facebook.com/")
    wait_for_load(driver)

    f_self_facebook_info = "self_facebook_info.bin"
    f_chat_history = "chat_histories.bin"
    if on_github_workflows:
        try:
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_self_facebook_info, STORAGE_BRANCE, f_self_facebook_info)
        except Exception as e:
            print_with_time(e)
        try:
            # Get chat_histories
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_chat_history + ".enc", STORAGE_BRANCE, f_chat_history + ".enc")
            decrypt_file(f_chat_history + ".enc", f_chat_history, encrypt_key)
        except Exception as e:
            print_with_time(e)

    chat_histories = pickle_from_file(f_chat_history, {})
    if chat_histories.get("status", None) is None:
        chat_histories["status"] = {}
    chat_histories_prev_hash = hash_dict(chat_histories)

    self_facebook_info = pickle_from_file(f_self_facebook_info, { })
    
    sk_list = [
            "about_work_and_education", 
            "about_places", 
            "about_contact_and_basic_info", 
            "about_family_and_relationships", 
            "about_details"
        ]
    self_url = get_facebook_profile_url(cookies)

    self_fbid = get_facebook_id(self_url)
    if self_fbid is None:
        self_fbid = get_facebook_id_from_cookies(cookies)
    print_with_time(f"URL là {self_url}")

    if self_facebook_info.get("Facebook name", None) is None or self_facebook_info.get("Facebook id", "") != self_fbid:
        print_with_time("Đang đọc thông tin cá nhân...")
        wait_for_load(driver)
        
        find_myname = driver.find_elements(By.CSS_SELECTOR, 'h1[class^="html-h1 "]')
        myname = find_myname[-1].text
        
        self_facebook_info = { "Facebook name" : myname, "Facebook id" : self_fbid, "Facebook url" :  self_url }
        # Loop through the profile sections
        for sk in sk_list:
            # Build the full URL for the profile section
            js_pushstate(driver, f"/profile.php?sk={sk}")
            time.sleep(3)
            
            # Wait for the page to load
            wait_for_load(driver)

            # Find the info elements
            info_elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="xyamay9 xqmdsaz x1gan7if x1swvt13"] > div')

            # Loop through each info element
            for info_element in info_elements:
                title = find_and_get_text(info_element, By.CSS_SELECTOR, 'div[class="xieb3on x1gslohp"]')
                if title is not None:
                    detail = []

                    # Append the text lists to the detail array
                    detail.extend(find_and_get_list_text(info_element, By.CSS_SELECTOR, 'div[class="x1hq5gj4"]'))
                    detail.extend(find_and_get_list_text(info_element, By.CSS_SELECTOR, 'div[class="xat24cr"]'))

                    # Add title and details to the facebook_info dictionary
                    self_facebook_info[title] = detail
        pickle_to_file(f_self_facebook_info, self_facebook_info)
        if on_github_workflows:
            upload_file(GITHUB_TOKEN, GITHUB_REPO, f_self_facebook_info, STORAGE_BRANCE)
    myname = self_facebook_info["Facebook name"]

    gemini_dev_mode = work_jobs.get("aichat", "normal") == "devmode"
    instruction = get_instructions_prompt(myname, ai_prompt, self_facebook_info, gemini_dev_mode)
    # Setup persona instruction
    genai.configure(api_key=genai_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=instruction,  # Your overall guidance to the model
        safety_settings={
            'harm_category_harassment': 'BLOCK_NONE',
            'harm_category_hate_speech': 'BLOCK_NONE',
            'harm_category_sexually_explicit': 'BLOCK_NONE',
            'harm_category_dangerous_content': 'BLOCK_NONE',
        }
    )

    for text in instruction:
        print_with_time(text)

    f_facebook_infos = "facebook_infos.bin"
    try:
        if on_github_workflows:
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_facebook_infos, STORAGE_BRANCE, f_facebook_infos)
    except Exception as e:
        print_with_time(e)
    facebook_infos = pickle_from_file(f_facebook_infos, {})

    ######################################
    print_with_time("Bắt đầu khởi động!")
    ######################################

    # Define a mapping of chat tabs to their corresponding URLs
    
    def __init_last_reload_ts_mapping():
        return {
            chat_tab : 0,
            mobileview : 0,
        }
    last_reload_ts_mapping = __init_last_reload_ts_mapping()
    ee2e_resolved = False

    def update():
        print_with_time("Cập nhật cookies lên máy chủ")
        cookies = driver.get_cookies()
        with open(filename, "w") as cookies_file:
            json.dump(cookies, cookies_file)
        with open(bakfilename, "w") as cookies_file:
            json.dump(bak_cookies, cookies_file)
        encrypt_file(filename, filename + ".enc", encrypt_key)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, filename + ".enc", STORAGE_BRANCE)
        encrypt_file(bakfilename, bakfilename + ".enc", encrypt_key)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, bakfilename + ".enc", STORAGE_BRANCE)
        global chat_histories_prev_hash
        if chat_histories_prev_hash == hash_dict(chat_histories):
            return False
        print_with_time("Sao lưu bộ nhớ trò chuyện")
        chat_histories_prev_hash = hash_dict(chat_histories)
        pickle_to_file(f_facebook_infos, facebook_infos)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_facebook_infos, STORAGE_BRANCE)
        if os.path.exists("files"):
            branch = upload_file(GITHUB_TOKEN, GITHUB_REPO, "files", generate_hidden_branch())
            try:
                shutil.rmtree("files") # Destroy directory after upload
            except Exception:
                pass # Ignore all error
            for msg_id, chat_history in chat_histories.items():
                if msg_id == "status":
                    continue
                for msg in chat_history:
                    if msg["message_type"] == "file" and msg["info"]["url"] == None:
                        # Update url of file
                        msg["info"]["url"] = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{msg["info"]["file_name"]}'
        # Backup chat_histories
        pickle_to_file(f_chat_history + ".enc", chat_histories, encrypt_key)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_chat_history + ".enc", STORAGE_BRANCE)
        return True

    driver.switch_to.window(mobileview)
    driver.get("https://www.facebook.com/language/")
    switched_to_english = False

    while True:
        try:
            time.sleep(1)
            if not switched_to_english:
                driver.switch_to.window(mobileview)
                english_buttons = driver.find_elements(By.XPATH, '//div[contains(text(), "English")]')
                if len(english_buttons) > 0:
                    driver.execute_script("arguments[0].click();", english_buttons[0])
                    print_with_time("Switched to English")
                    switched_to_english = True
            elif "friends" in work_jobs:
                if (int(time.time()) - last_reload_ts_mapping.get(mobileview, 0)) > 60*30:
                    driver.switch_to.window(mobileview)
                    last_reload_ts_mapping[mobileview] = int(time.time())
                    driver.get("https://www.facebook.com/friends")
                    wait_for_load(driver)
                    time.sleep(1)
                    try:
                        for button in driver.find_elements(
                            By.XPATH, "//div[starts-with(@aria-label, 'Confirm ') and .//span[text()='Confirm']]"
                        ):
                            print_with_time(button.get_attribute("aria-label"))
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(0.1)
                    except Exception:
                        pass
                    time.sleep(0.1)
                    try:
                        for button in driver.find_elements(
                            By.XPATH, "//div[starts-with(@aria-label, 'Remove ') and .//span[text()='Delete']]"
                        ):
                            print_with_time(button.get_attribute("aria-label"))
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(0.1)
                    except Exception:
                        pass

            driver.switch_to.window(chat_tab)
            if "aichat" in work_jobs:
                if last_reload_ts_mapping.get(chat_tab, 0) == 0:
                    print_with_time(f"Khởi động Messenger")
                    js_pushstate(driver, "/messages/requests")
                    last_reload_ts_mapping[chat_tab] = int(time.time())
                try:
                    if len(onetimecode) >= 6 and not ee2e_resolved:
                        otc_input = driver.find_element(By.CSS_SELECTOR, 'input[autocomplete="one-time-code"]')
                        driver.execute_script("arguments[0].setAttribute('class', '');", otc_input)
                        print_with_time("Giải mã đoạn chat được mã hóa...")
                        actions.move_to_element(otc_input).click().perform()
                        time.sleep(2)
                        for digit in onetimecode:
                            actions.move_to_element(otc_input).send_keys(digit).perform()  # Send the digit to the input element
                            time.sleep(1)  # Wait for 1s before sending the next digit
                        print_with_time("Hoàn tất giải mã!")
                        time.sleep(5)
                        ee2e_resolved = True
                        continue
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, 'div.__fb-light-mode.x1n2onr6.x1vjfegm')
                        # Inject style to hide the element
                        driver.execute_script("arguments[0].style.display = 'none';", element)
                except Exception:
                    pass

                chat_list = []
                chat_list_all = []
                # find all chat buttons
                chat_btns = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/messages/"]')
                for chat_btn in chat_btns:
                    try:
                        new_chat_indicator = chat_btn.find_elements(By.CSS_SELECTOR, 'span.x6s0dn4.xzolkzo.x12go9s9.x1rnf11y.xprq8jg.x9f619.x3nfvp2.xl56j7k.x1spa7qu.x1kpxq89.xsmyaan')
                        
                        href = chat_btn.get_attribute("href")
                        message_id = get_last_part(href)
                        chat_name = chat_btn.find_element(By.CSS_SELECTOR, 'span[dir="auto"]').text
                        chat_info = { "id" : message_id, "href" : href, "name" : chat_name }
                        chat_list_all.append(chat_info)
                        
                        if len(new_chat_indicator) <= 0 and ("aichat_no_welcome" in work_jobs or chat_histories.get(message_id, None)):
                            continue
                        chat_list.append(chat_info)
                    except Exception:
                        continue

                def get_message_input():
                    return driver.find_element(By.CSS_SELECTOR, 'div[role="textbox"] p')

                if len(chat_list) > 0:
                    print_with_time(f"Nhận được {len(chat_list)} tin nhắn mới")
                    for chat_info in chat_list:
                        if True:
                            is_group_chat = False
                            chat_href = chat_info["href"]
                            main = driver.find_elements(By.CSS_SELECTOR, 'div[role="main"]')
                            if len(main) > 0:
                                driver.execute_async_script("""
                                    var callback = arguments[arguments.length - 1];  // Get the callback function
                                    window.__old_main = arguments[0]; // Keep in memory
                                    arguments[0].remove();  // Remove the element
                                    callback();  // Call the callback once done
                                """, main[0])
                            js_pushstate(driver, chat_href)
                            message_id = get_last_part(chat_href)
                            if not chat_histories.get(message_id, None):
                                chat_histories[message_id] = [{"message_type" : "new_chat", "info" : "You are now connected on Messenger"}]
                            
                            # Wait until box is visible
                            try:
                                main = WebDriverWait(driver, 15).until(
                                    EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]'))
                                )
                            except Exception as e:
                                print_with_time(e)
                            
                            try:
                                profile_btn = driver.find_elements(By.XPATH, "//a[.//h2]")
                                facebook_info = None
                                facebook_id = None
                                if len(profile_btn) > 0:
                                    profile_btn = profile_btn[0]
                                    profile_href = f'{profile_btn.get_attribute("href")}'
                                    profile_link = urljoin(driver.current_url, profile_href)

                                    facebook_info = facebook_infos.get(profile_link)
                                    if facebook_info != None:
                                        last_access_ts = facebook_info.get("Last access", 0)
                                        
                                        # Get the current time Unix timestamp minus 30 days
                                        three_days_ago = int(time.time()) - 30 * 24 * 60 * 60
                                        
                                        if last_access_ts < three_days_ago:
                                            facebook_info = None

                                    if facebook_info == None:
                                        js_pushstate(driver, profile_href)

                                        print_with_time(f"Đang lấy thông tin cá nhân từ {profile_link}")
                                        
                                        wait_for_load(driver)
                                        time.sleep(3)
                                        find_who_chatted = driver.find_elements(By.CSS_SELECTOR, 'h1[class^="html-h1 "]')
                                        who_chatted = find_who_chatted[-1].text
                                        
                                        facebook_info = { 
                                            "Facebook name" : who_chatted,
                                            "Facebook url" :  profile_link,
                                            "Last access" : int(time.time())
                                        }
                                        for sk in sk_list:
                                            # Build the full URL for the profile section
                                            js_pushstate(driver, f"{profile_href}?sk={sk}")
                                            time.sleep(3)

                                            # Wait for the page to load
                                            wait_for_load(driver)
                                            #time.sleep(0.5)

                                            # Find the info elements
                                            info_elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="xyamay9 xqmdsaz x1gan7if x1swvt13"] > div')

                                            # Loop through each info element
                                            for info_element in info_elements:
                                                title = find_and_get_text(info_element, By.CSS_SELECTOR, 'div[class="xieb3on x1gslohp"]')
                                                if title is not None:
                                                    detail = []

                                                    # Append the text lists to the detail array
                                                    detail.extend(find_and_get_list_text(info_element, By.CSS_SELECTOR, 'div[class="x1hq5gj4"]'))
                                                    detail.extend(find_and_get_list_text(info_element, By.CSS_SELECTOR, 'div[class="xat24cr"]'))

                                                    # Add title and details to the facebook_info dictionary
                                                    facebook_info[title] = detail
                                        
                                        facebook_infos[profile_link] = facebook_info
                                        js_pushstate(driver, chat_href)
                                    else:
                                        who_chatted = facebook_info.get("Facebook name")

                                    facebook_info["Last access"] = int(time.time())
                                else:
                                    is_group_chat = True
                                    group_name = main.find_elements(By.CSS_SELECTOR, "h2")
                                    who_chatted = group_name[0].text if len(group_name) > 0 else chat_info["name"]
                                    facebook_info = { "Facebook group name" : who_chatted, "Facebook url" :  driver.current_url }

                                parsed_url = urlparse(facebook_info.get("Facebook url", None))
                                # Remove the trailing slash from the path, if it exists
                                urlpath = parsed_url.path
                                # Split the path and extract the ID
                                facebook_id = get_last_part(urlpath)
                            except Exception as e:
                                print_with_time(e)
                                continue

                        print_with_time(f"Tin nhắn mới từ {who_chatted} (ID: {facebook_id})")
                        if "debug" in work_jobs:
                            print_with_time(json.dumps(facebook_info, ensure_ascii=False, indent=2))

                        while True:
                            try:
                                parsed_url = urlparse(driver.current_url)
                                urlpath = parsed_url.path
                                message_id = get_last_part(urlpath)
                                # Wait until box is visible
                                try:
                                    time.sleep(1)
                                    main = WebDriverWait(driver, 15).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]'))
                                    )
                                    msg_table = main.find_element(By.CSS_SELECTOR, 'div[role="grid"]')
                                except Exception as e:
                                    print_with_time("Không thể tải đoạn chat")
                                    break
                                prompt_list = []
                                def process_chat_history(chat_history):
                                    result = []
                                    for msg in chat_history:
                                        final_last_msg = msg
                                        if msg["message_type"] == "text_message" and is_cmd(msg["info"]["msg"]):
                                            final_last_msg = copy.deepcopy(msg)
                                            final_last_msg["info"]["msg"] = "<This is command message. It has been hidden>"
                                        result.append(json.dumps(final_last_msg, ensure_ascii=False))
                                        if msg["message_type"] == "file" and msg["info"].get("loaded", False):
                                            file_name = msg["info"]["file_name"]
                                            mime_type = msg["info"]["mime_type"]
                                            try:
                                                # find the cached files first
                                                file_upload = genai.get_file(file_name)
                                            except Exception:
                                                try:
                                                    if msg["info"].get("url", None) is not None:
                                                        # generate new file name if possible to avoid any conflict
                                                        file_name = f"files/{generate_random_string(40)}"
                                                        msg["info"]["file_name"] = file_name
                                                        get_raw_file(msg["info"]["url"], file_name)
                                                    file_upload = genai.upload_file(path = file_name, mime_type = mime_type, name = file_name)
                                                except Exception as e:
                                                    result.append(f"{file_name} cannot be loaded")
                                                    print_with_time(e)
                                                    continue
                                            result.append(file_upload)
                                    return result

                                def release_unload_files(chat_history, do_all = False):
                                    result = []
                                    for msg in chat_history:
                                        if msg["message_type"] == "file" and (do_all or msg["info"].get("loaded", False) == False):
                                            try:
                                                file_name = msg["info"]["file_name"]
                                                # find the cached files first
                                                file_upload = genai.get_file(file_name)
                                                genai.delete_file(file_upload)
                                            except Exception:
                                                pass
                                    
                                chat_history = chat_histories.get(message_id, [])
                                old_chat_history = chat_histories.get(facebook_id, []) if message_id != facebook_id else []
                                # The conversation might have been upgraded to end-to-end encryption
                                # We update it from old unencrypted chat to encrypted one
                                if message_id != facebook_id and len(old_chat_history) > 0:
                                    old_chat_history = chat_histories.pop(facebook_id, [])
                                    old_chat_history.extend(chat_history)
                                    chat_history = old_chat_history
                                    chat_histories[message_id] = chat_history

                                header_prompt = get_header_prompt(get_day_and_time(), who_chatted, facebook_info)

                                prompt_list.append(f'The Messenger conversation with "{who_chatted}" is as json here:')

                                print_with_time("Đang đọc tin nhắn...")

                                command_result = []
                                reset = False
                                should_stop = False
                                should_not_chat = chat_histories["status"].get(message_id, True) == False or chat_histories["status"].get(facebook_id, True) == False
                                max_video = 10
                                num_video = 0
                                max_file = 10
                                num_file = 0
                                regex_rules_applied = work_jobs.get(f"aichat_{facebook_id}_rules", "")
                                regex_rules_applied = regex_rules_applied.split() if regex_rules_applied else []
                                reset_regex_list = { global_reset_msg : global_reset_msg }
                                stop_regex_list = { global_stop_msg : global_stop_msg }
                                start_regex_list = { global_start_msg : global_start_msg }
                                bye_msg_list = [ global_bye_msg ]
                                
                                if regex_rules_applied:
                                    print_with_time(f"Áp dụng quy tắc: {regex_rules_applied}")
                                    for name in regex_rules_applied:
                                        reset_regex = work_jobs.get(f"aichat_{name}_resetat", None)
                                        reset_msg = work_jobs.get(f"aichat_{name}_resetmsg", None)
                                        reset_regex_list[reset_regex] = reset_msg
                                        
                                        stop_regex = work_jobs.get(f"aichat_{name}_stopat", None)
                                        stop_msg = work_jobs.get(f"aichat_{name}_stopmsg", None)
                                        stop_regex_list[stop_regex] = stop_msg
                                        
                                        start_regex = work_jobs.get(f"aichat_{name}_startat", None)
                                        start_msg = work_jobs.get(f"aichat_{name}_startmsg", None)
                                        start_regex_list[start_regex] = start_msg
                                        
                                        bye_msg_list.append(work_jobs.get(f"aichat_{name}_byemsg", None))

                                driver.execute_script("""
                                    window.last_play_src = null;
                                    HTMLMediaElement.prototype.play = function() {
                                      window.last_play_src = this.src;
                                      return Promise.resolve(); // Ngăn phát
                                    };
                                """)
                                # call driver.execute_script("return window.last_play_src;")

                                def process_elements(msg_table):
                                    chat_history_new = []
                                    files_mapping = {}
                                    global should_not_chat
                                    for msg_element in reversed(msg_table.find_elements(By.CSS_SELECTOR, 'div[role="row"]')):
                                        try:
                                            checkpointed = msg_element.get_attribute("checkpoint")
                                        except Exception:
                                            checkpointed = "none"
                                        finally:
                                            if checkpointed == "checkpointed":
                                                break
                                            driver.execute_script("arguments[0].setAttribute('checkpoint', 'checkpointed')", msg_element)

                                        try:
                                            timedate = msg_element.find_element(By.CSS_SELECTOR, 'span[class="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1pg5gke xvq8zen xo1l8bm x12scifz"]')
                                            chat_history_new.insert(0, {"message_type" : "conversation_event", "info" : timedate.text})
                                        except Exception:
                                            pass

                                        try:
                                            quotes_text = msg_element.find_element(By.CSS_SELECTOR, 'div[class="xi81zsa x126k92a"]').text
                                        except Exception:
                                            quotes_text = None

                                        # Finding name
                                        try: 
                                            msg_element.find_element(By.CSS_SELECTOR, 'div[class="html-div xexx8yu x4uap5 x18d9i69 xkhd6sd x1gslohp x11i5rnm x12nagc x1mh8g0r x1yc453h x126k92a xyk4ms5"]').text
                                            break
                                        except Exception:
                                            name = None
                                            mark = "text_message"
                                        # Scrape user name
                                        name = None
                                        selectors = ['h4', 'h5[dir="auto"]', 'span.html-span']
                                        for selector in selectors:
                                            if not name:
                                                try:
                                                    name = msg_element.find_element(By.CSS_SELECTOR, selector).text
                                                except Exception:
                                                    name = None
                                        # Scrape message
                                        msg = None
                                        try:
                                            msg_frame = msg_element.find_element(By.CSS_SELECTOR, 'div[dir="auto"][class^="html-div "]')
                                            msg = msg_frame.text
                                            mentioned_to_me = msg_frame.find_elements(By.CSS_SELECTOR, f'a[href="https://www.facebook.com/{self_fbid}/"]')
                                            if len(mentioned_to_me) > 0:
                                                chat_histories["status"][message_id] = True
                                                chat_histories["status"][facebook_id] = True
                                                should_not_chat = False
                                                chat_history_new.insert(0, {"message_type" : "new_chat", "info" : "You are mentioned in chat"})
                                        except Exception:
                                            pass
                                        if msg is None:
                                            try:
                                                msg_title = msg_element.find_element(By.CSS_SELECTOR, 'span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6')
                                                msg = msg_title.text
                                                msg_small = msg_element.find_element(By.CSS_SELECTOR, 'span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6.x1j85h84')
                                                msg += "\n" + msg_small.text
                                            except Exception:
                                                pass
                                        
                                        image_elements = msg_element.find_elements(By.CSS_SELECTOR, 'img.xz74otr.xmz0i5r.x193iq5w')
                                        for image_element in image_elements:
                                            try:
                                                data_uri = image_element.get_attribute("src")
                                                image_name = f"files/{generate_random_string(40)}"
                                                if data_uri.startswith("data:image/jpeg;base64,"):
                                                    # Extract the base64 string (remove the prefix)
                                                    base64_str = data_uri.split(",")[1]
                                                    # Decode the base64 string into binary data
                                                    image_data = base64.b64decode(base64_str)
                                                    files_mapping[image_name] = ("data", image_data)
                                                else:
                                                    files_mapping[image_name] = ("url", data_uri)
                                               
                                                chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send image", "file_name" : image_name, "mime_type" : "image/jpeg" , "url" : None, "loaded" : True }, "mentioned_message" : quotes_text})
                                            except Exception:
                                                pass

                                        try:
                                            video_element = msg_element.find_element(By.CSS_SELECTOR, 'video')
                                            video_url = video_element.get_attribute("src")
                                            video_name = f"files/{generate_random_string(40)}"
                                            files_mapping[video_name] = ("url", video_url)

                                            chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send video", "file_name" : video_name, "mime_type" : "video/mp4", "url" : None, "loaded" : False }, "mentioned_message" : quotes_text})
                                        except Exception:
                                            pass

                                        try:
                                            audio_element = msg_element.find_element(By.CSS_SELECTOR, 'path[d="M10 25.5v-15a1.5 1.5 0 012.17-1.34l15 7.5a1.5 1.5 0 010 2.68l-15 7.5A1.5 1.5 0 0110 25.5z"]')
                                            driver.execute_script('arguments[0].dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));', audio_element)
                                            time.sleep(0.1)
                                            audio_url = driver.execute_script("return window.last_play_src;")
                                            driver.execute_script("window.last_play_src = null;")
                                            audio_name = f"files/{generate_random_string(40)}"
                                            files_mapping[audio_name] = ("url", audio_url)

                                            chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send audio", "file_name" : audio_name, "mime_type" : "audio/mp4", "url" : None, "loaded" : True }, "mentioned_message" : quotes_text})
                                        except Exception:
                                            pass

                                        try:
                                            file_element = msg_element.find_element(By.CSS_SELECTOR, 'a[download]')
                                            file_url = file_element.get_attribute("href")
                                            if file_url.startswith("blob:"): # e2ee chats save files in blob
                                                file_down_name = file_element.get_attribute("download")
                                            else:
                                                parsed_url = urlparse(file_url)
                                                file_down_name = parsed_url.path.rstrip("/").split("/")[-1]
                                            file_ext, mime_type = get_mine_type(file_down_name)
                                            if check_supported_file(mime_type):
                                                file_name = f"files/{generate_random_string(40)}"
                                                files_mapping[file_name] = ("url", file_url)
                                                chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send file", "file_name" : file_name, "mime_type" : mime_type, "url" : None, "loaded" : False }, "mentioned_message" : quotes_text})
                                            continue
                                        except Exception:
                                            pass

                                        try: 
                                            react_elements = msg_element.find_elements(By.CSS_SELECTOR, 'img[height="32"][width="32"]')
                                            emojis = ""
                                            if msg == None and len(react_elements) > 0:
                                                for react_element in react_elements:
                                                    emojis += react_element.get_attribute("alt")
                                                msg = emojis
                                        except Exception:
                                            pass

                                        if msg == None:
                                            try:
                                                msg_element.find_element(By.CSS_SELECTOR, 'div[aria-label="Like, thumbs up"]')
                                                msg = "👍"
                                            except Exception:
                                                msg = None

                                        if msg == None:
                                            continue
                                        if name == None:
                                            name = "None"
                                        
                                        chat_history_new.insert(0, {"message_type" : mark, "info" : {"name" : name, "msg" : msg}, "mentioned_message" : quotes_text })
                                    return chat_history_new, files_mapping

                                try: # Emulate typing...
                                    if not should_not_chat:
                                        actions.move_to_element(get_message_input()).click().send_keys(" ").perform()
                                except Exception:
                                    pass
                                chat_history_new, files_mapping = process_elements(msg_table)

                                print_with_time("Đã đọc xong!")

                                def reset_chat(msg = None):
                                    global reset
                                    reset = True
                                    if msg == None:
                                        msg = message_id
                                    chat_histories[msg] = [{"message_type" : "new_chat", "info" : "New chat"}]
                                    return f'Bot has been reset'

                                def mute_chat(mode):
                                    global should_not_chat
                                    if mode == "true" or mode == "1":
                                        chat_histories["status"][message_id] = False
                                        chat_histories["status"][facebook_id] = False
                                        should_not_chat = True
                                        return f'Bot has been muted'
                                    if mode == "false" or mode == "0":
                                        chat_histories["status"][message_id] = True
                                        chat_histories["status"][facebook_id] = True
                                        return f'Bot has been unmuted'
                                    return f'Unknown mute mode! Use "1" to mute the bot or "0" to unmute the bot.'

                                def mute_by_id(chatid):
                                    if chatid == None:
                                        chatid = message_id
                                    chat_histories["status"][chatid] = False
                                    return f"Bot is muted in chat with id {chatid}"

                                def unmute_by_id(chatid):
                                    if chatid == None:
                                        chatid = message_id
                                    chat_histories["status"][chatid] = True
                                    return f"Bot is unmuted in chat with id {chatid}"

                                def dump_chat(chatid):
                                    if chatid == None:
                                        chatid = message_id
                                    return json.dumps(chat_histories.get(chatid, []), ensure_ascii=False, indent=2)

                                def get_info(name):
                                    if name == "inbox":
                                        return json.dumps(chat_list_all, ensure_ascii=False, indent=2)
                                    if name == "cookies":
                                        return json.dumps(cookies, ensure_ascii=False, indent=2)
                                    if name == "enckey":
                                        return PASSWORD
                                    return f"Invalid argument: {name}"

                                def terminate(__):
                                    global should_stop
                                    should_stop = True
                                    return "Good bye!"

                                # Dictionary mapping arg1 to functions
                                func = {
                                    "reset": reset_chat,
                                    "mute" : mute_by_id,
                                    "unmute" : unmute_by_id,
                                    "get" : get_info,
                                    "dump" : dump_chat,
                                    "terminate" : terminate,
                                }

                                def parse_and_execute(command):
                                    if facebook_id != admin_fbid:
                                        return "?"
                                    # Parse the command
                                    args = shlex.split(command)
                                    
                                    # Check if the command starts with /cmd
                                    if len(args) < 2 or args[0] != "/cmd":
                                        return "Invalid command format. Use: /cmd arg1 arg2"
                                    
                                    # Extract arg1 and arg2
                                    arg1 = args[1]
                                    arg2 = args[2] if len(args) > 2 else None
                                    
                                    # Check if arg1 is in func and execute
                                    if arg1 in func:
                                        try:
                                            return func[arg1](arg2)
                                        except Exception as e:
                                            return f"Error while executing function: {e}"
                                    else:
                                        return f"Unknown command: {arg1}"

                                if len(chat_history_new) <= 0:
                                    break
                                last_msg = chat_history_new[-1]
                                if last_msg["message_type"] == "your_text_message":
                                    break

                                for msg in chat_history_new:
                                    if msg["message_type"] == "text_message":
                                        if is_cmd(msg["info"]["msg"]):
                                            command_result.append(parse_and_execute(msg["info"]["msg"]))
                                        for regex_list, action, value in [
                                            (reset_regex_list, reset_chat, "0"),
                                            (stop_regex_list, mute_chat, "true"),
                                            (start_regex_list, mute_chat, "false")
                                        ]:
                                            for regex, msg_text in regex_list.items():
                                                if regex and re.search(regex, msg["info"]["msg"]):
                                                    action(value)  # Calls reset_chat("0") or mute_chat("true"/"false")
                                                    if msg_text:
                                                        command_result.append(msg_text)

                                try:
                                    actions.move_to_element(get_message_input()).click()\
                                       .key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)\
                                       .send_keys(Keys.DELETE)\
                                       .perform()
                                    if command_result:
                                        for result in command_result:
                                            send_keys_long_text(get_message_input(), remove_non_bmp_characters(replace_emoji_with_shortcut(result)))
                                            get_message_input().send_keys("\n") # Press Enter to send image
                                except Exception:
                                    pass
                                if should_stop:
                                    time.sleep(10)
                                    raise KeyboardInterrupt
                                is_command_msg = last_msg["message_type"] == "text_message" and is_cmd(last_msg["info"]["msg"])
                                if is_command_msg:
                                    break
                                if reset:
                                    break
                                if should_not_chat:
                                    break
                                if genai_key is None:
                                    break
                                try: # Emulate typing...
                                    actions.move_to_element(get_message_input()).click().send_keys(" ").perform()
                                except Exception:
                                    pass

                                for file_name, file_info in files_mapping.items():
                                    info_type = file_info[0]
                                    file_data = file_info[1] if info_type == "data" else (
                                        get_file_data(driver, file_info[1]) if file_info[1].startswith("blob:")
                                        else requests.get(file_info[1]).content
                                    )
                                    file_object = BytesIO(file_data)
                                    os.makedirs(os.path.dirname(file_name), exist_ok=True)
                                    bytesio_to_file(file_object, file_name)

                                max_lines = 75
                                summary_lines = 25
                                left_lines = max_lines - summary_lines
                                if len(chat_history) > max_lines:
                                    try:
                                        # Summary old 100 messages
                                        __num_video = 0
                                        __num_file = 0
                                        for msg in reversed(chat_history[:summary_lines]):
                                            if msg["message_type"] == "file":
                                                if msg["info"]["msg"] == "send video":
                                                    __num_video += 1  # Increment first
                                                    msg["info"]["loaded"] = __num_video <= max_video  # Compare after incrementing
                                                elif msg["info"]["msg"] == "send file":
                                                    __num_file += 1  # Increment first
                                                    msg["info"]["loaded"] = __num_file <= max_file  # Compare after incrementing
                                        prompt_to_summary = process_chat_history(chat_history[:summary_lines])
                                        prompt_to_summary.append(">> You are entering the chat summarization phase to optimize memory usage while maintaining a natural conversational flow. Your task is to summarize the following conversation as if you were recalling past messages naturally. Tell me key information about this chat conversation, including all previous summaries, and retain important details for future reference. The summary should be in English, direct, unquoted, and without markdown.")
                                        response = model.generate_content(prompt_to_summary)
                                        release_unload_files(chat_history[:summary_lines], True)
                                        if not response.candidates:
                                            caption = "Old chat conversation is deleted"
                                        else:
                                            caption = response.text
                                    except Exception as e:
                                        print_with_time(e)
                                        caption = "Old chat conversation is deleted"
                                    chat_history = chat_history[-left_lines:]
                                    chat_history.insert(0, {"message_type" : "summary_old_chat", "info" : caption})

                                chat_history.extend(chat_history_new)

                                for msg in reversed(chat_history):
                                    if msg["message_type"] == "file":
                                        if msg["info"]["msg"] == "send video":
                                            num_video += 1  # Increment first
                                            msg["info"]["loaded"] = num_video <= max_video  # Compare after incrementing
                                        elif msg["info"]["msg"] == "send file":
                                            num_file += 1  # Increment first
                                            msg["info"]["loaded"] = num_file <= max_file  # Compare after incrementing
                                #release_unload_files(chat_history)
                                prompt_list.extend(process_chat_history(chat_history))

                                if "debug" in work_jobs:
                                    for prompt in prompt_list:
                                        print_with_time(prompt)
                                print_with_time(f"<{len(chat_history)} tin nhắn từ {who_chatted}>")
                                    
                          
                                prompt_list.insert(0, header_prompt)
                                exam = json.dumps({"message_type" : "your_text_message", "info" : {"name" : myname, "msg" : "Your \"message\" is here - “Tin nhắn” của bạn ở đây 😊"}, "mentioned_message" : None }, indent = 4, ensure_ascii=False)
                                prompt_list.append(f'>> Generate a response in properly formatted JSON to reply back to user.\nExample:\n{exam}\n')
                                
                                caption = None
                                for _x in range(10):
                                    try:
                                        button = get_message_input()
                                        driver.execute_script("arguments[0].click();", button)
                                        get_message_input().send_keys(Keys.CONTROL + "a")  # Select all text
                                        get_message_input().send_keys(Keys.DELETE)  # Delete the selected text
                                        if caption is None:
                                            response = model.generate_content(prompt_list, generation_config=genai.GenerationConfig(
                                                response_mime_type="application/json"
                                            ),)
                                            if not response.candidates:
                                                chat_history = [{"message_type" : "summary_old_chat", "info" : "The previous conversation has been deleted"}]
                                                caption = json.dumps({"info" : {"msg" : "Sorry!"}}, indent = 4, ensure_ascii=False)
                                            else:
                                                caption = response.text
                                        if caption is not None:
                                            img_search = {}
                                            is_image_dropped = False
                                            reply_msg, img_search["on"] = extract_keywords(r'\[image\](.*?)\[/image\]', caption)
                                            if work_jobs["aichat"] == "devmode":
                                                reply_msg, img_search["off"] = extract_keywords(r'\[adultimg\](.*?)\[/adultimg\]', reply_msg)
                                            else:
                                                reply_msg, _img_search = extract_keywords(r'\[adultimg\](.*?)\[/adultimg\]', reply_msg)
                                                img_search["on"].extend(_img_search)
                                            reply_msg, img_search["link"] = extract_keywords(r'\[imglink\](.*?)\[/imglink\]', reply_msg)
                                            reply_msg, itunes_keywords = extract_keywords(r'\[itunes\](.*?)\[/itunes\]', reply_msg)
                                            reply_msg, bot_commands = extract_keywords(r'\[cmd\](.*?)\[/cmd\]', reply_msg)
                                            
                                            json_msg = fix_json(reply_msg)
                                            try:
                                                reply_msg = json_msg["info"]["msg"]
                                            except Exception:
                                                caption = None
                                                raise JSON5DecodeError("Error getting message") # Ask Gemini to re-generate JSON

                                            for adult, img_keywords in img_search.items():
                                                for img_keyword in img_keywords:
                                                    try:
                                                        for _x in range(5):
                                                            try:
                                                                image_link = img_keyword if adult == "link" else get_random_image_link(img_keyword, 30, adult)
                                                                image_io = download_file_to_bytesio(image_link)
                                                            except Exception:
                                                                continue
                                                            if "debug" in work_jobs:
                                                                print_with_time(f"AI gửi ảnh {img_keyword} từ: {image_link}")
                                                            drop_image(driver, button, image_io)
                                                            is_image_dropped = True
                                                            break
                                                    except Exception:
                                                        print_with_time(f"Không thể gửi ảnh: {img_keyword}")
                                            if is_image_dropped:
                                                get_message_input().send_keys("\n") # Press Enter to send image
                                            is_image_dropped = False
                                            for itunes_keyword in itunes_keywords:
                                                try:
                                                    for _x in range(5):
                                                        music_io = None
                                                        try:
                                                            itunes_link = search_music_itunes(itunes_keyword, 1)
                                                            if len(itunes_link) == 0:
                                                                break
                                                            itunes_link = itunes_link[0].get("preview_url", None)
                                                            if not itunes_link:
                                                                break
                                                            music_io = download_file_to_bytesio(itunes_link)
                                                        except Exception:
                                                            continue
                                                        if music_io is None:
                                                            raise Exception("No music")
                                                        if "debug" in work_jobs:
                                                            print_with_time(f"AI gửi nhạc {itunes_keyword} từ: {itunes_link}")
                                                        drop_file(driver, button, music_io, "audio/mp4")
                                                        is_image_dropped = True
                                                        break
                                                except Exception:
                                                    print_with_time(f"Không thể gửi nhạc: {itunes_keyword}")
                                            if is_image_dropped:
                                                get_message_input().send_keys("\n") # Press Enter to send music
                                            print_with_time("* AI Trả lời:", reply_msg if "debug" in work_jobs else "<1 tin nhắn>")
                                            send_keys_long_text(get_message_input(), remove_non_bmp_characters(replace_emoji_with_shortcut(reply_msg)))
                                            # There maybe newer msg while AI process chat
                                            chat_history_new, files_mapping = process_elements(msg_table)
                                            # Press Enter to send message
                                            get_message_input().send_keys("\n")
                                            if "bye" in bot_commands:
                                                print_with_time("* Bot yêu cầu dừng trả lời tin nhắn")
                                                chat_history.append({"message_type" : "conversation_event", "info" : "You have left the conversation"})
                                                if is_group_chat and "aichat_nobye" not in work_jobs:
                                                    chat_histories["status"][message_id] = False
                                                    chat_histories["status"][facebook_id] = False
                                                for bye_msg in bye_msg_list:
                                                    if bye_msg:
                                                        get_message_input().send_keys(remove_non_bmp_characters(bye_msg) + "\n")
                                            chat_history.extend(chat_history_new)
                                            chat_history.append({"message_type" : "your_text_message", "info" : {"name" : myname, "msg" : reply_msg}, "mentioned_message" : None })
                                            chat_histories[message_id] = chat_history
                                            for file_name, file_info in files_mapping.items():
                                                info_type = file_info[0]
                                                file_data = file_info[1] if info_type == "data" else (
                                                    get_file_data(driver, file_info[1]) if file_info[1].startswith("blob:")
                                                    else requests.get(file_info[1]).content
                                                )
                                                file_object = BytesIO(file_data)
                                                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                                                bytesio_to_file(file_object, file_name)
                                        break
                                    except NoSuchElementException:
                                        print_with_time("Không thể trả lời")
                                        break
                                    except JSON5DecodeError as e:
                                        caption = None
                                        print_with_time(e)
                                    except StaleElementReferenceException:
                                        pass
                                    except Exception as e:
                                        print_with_time(e)
                                        pass
                                    print_with_time("Thử lại:", _x + 1)
                                    time.sleep(2)
                                break
                            except StaleElementReferenceException:
                                pass
                            except Exception as e:
                                print_with_time(e)
                                break
                    # Back to home
                    js_pushstate(driver, "/messages/requests")
        except Exception as e:
            print_with_time(e)
        
        try:
            current_url = driver.current_url
            if is_facebook_domain(current_url) and get_path(current_url).startswith("/checkpoint/"):
                print_with_time("Tài khoản bị đình chỉ bởi Facebook")
                raise KeyboardInterrupt
            if is_facebook_logged_out(driver.get_cookies()):
                if bak_cookies is not None:
                    print_with_time("Tài khoản bị đăng xuất, sử dụng cookies dự phòng")
                    # TODO: obtain new cookies
                    driver.delete_all_cookies()
                    for cookie in bak_cookies:
                        cookie.pop('expiry', None)  # Remove 'expiry' field if it exists
                        driver.add_cookie(cookie)
                    bak_cookies = None
                    last_reload_ts_mapping = __init_last_reload_ts_mapping()
                    driver.get("https://www.facebook.com/")
                    wait_for_load(driver)
                    time.sleep(1)
                    continue
                else:
                    print_with_time("Tài khoản bị đăng xuất")
                    raise KeyboardInterrupt
        except Exception as e:
            print_with_time("Lỗi xảy ra:", e)
            pass # Ignore all errors
        try:
            with open("exitnow.txt", "r", encoding='utf-8') as file:
                content = file.read().strip()  # Read and strip any whitespace/newline
                if content == "1":
                    raise KeyboardInterrupt
        except Exception:
            pass # Ignore all errors

except KeyboardInterrupt:
    print_with_time("KeyboardInterrupt: clean up, please wait")
finally:
    if on_github_workflows:
        update()
    if driver is not None:
        print_with_time("Quit...")
        driver.quit()
    print_with_time("Done!")
    
