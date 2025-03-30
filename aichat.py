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
from pickle_utils import *  # For pickling data
from github_utils import *  # For GitHub file operations
from fbparser import get_facebook_profile_url, get_facebook_id, get_facebook_name
from fb_getcookies import __chrome_driver__ 
from fb_getcookies import * # For Facebook cookie handling
from aichat_utils import *  # For custom utility functions
from js_selenium import js_pushstate, inject_my_stealth_script
from shorturl import start_shorturl_thread, register_shorturl, get_local_file_url
from PIL import Image
import threading
from pasterman import pasterman
from google import genai
from google.genai import types # Needed for multimodal content like images
from google.genai.types import HarmCategory, HarmBlockThreshold, GenerateContentConfig, SafetySetting, UploadFileConfig, FileState, GoogleSearch, Tool
import traceback
import re
from gemini_generate_image import generate_image
from google.genai.errors import ClientError, ServerError
from image_upload import upload_to_catbox
from image_visual import simulate_camera_effect_bytesio
import nickname
import inspect

MESSENGER_HOME_PAGE = "/messages/t/_"
GENAI_MODEL = "gemini-2.0-flash"

def is_only_whitespace(s):
    return all(
        c.isspace()
        for c in s
    )

def get_day_and_time():
    # Get current date and time
    current_datetime = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
    # Format the output
    return current_datetime.strftime("%A, %d %B %Y - %H:%M:%S")

def print_with_time(*args, sep=" ", end="\n", file=None, flush=False): 
    print(get_day_and_time(), ":", *args, sep=sep, end=end, file=file, flush=flush)

sys.stdout.reconfigure(encoding='utf-8')

# GEMINI
genai_keys_text = os.getenv("GENKEY", "")
if genai_keys_text:
    try:
        with open("gemini_key.txt", "w", encoding="utf-8") as f:
            f.write(genai_keys_text)
    except Exception: pass
if not genai_keys_text:
    try:
        with open("gemini_key.txt", "r", encoding="utf-8") as f:
            print("Đã đọc key từ file") 
            genai_keys_text = f.read()
    except Exception: pass


genai_keys = [
    line.split('#', 1)[0].strip()              # take before `#`, trim spaces
    for line in genai_keys_text.splitlines()              # handle \n, \r\n, \r
    if line.strip() and not line.strip().startswith('#')  # ignore empty & comment-only lines
]

genai_keys_for_genai = genai_keys.copy()
genai_keys_for_genimg = genai_keys.copy()
client, genimg_client = None, None

google_search_tool = Tool(
    google_search = GoogleSearch()
)

def pop_key_for_genai():
    global genai_keys_for_genai, client
    if len(genai_keys_for_genai) <= 0:
        genai_keys_for_genai = genai_keys.copy()
        return False
    genai_key = genai_keys_for_genai.pop(0)
    #print_with_time(genai_key)
    client = genai.Client(api_key=genai_key)
    return True
pop_key_for_genai()

def pop_key_for_genimg():
    global genai_keys_for_genimg, genimg_client
    if len(genai_keys_for_genimg) <= 0:
        genai_keys_for_genimg = genai_keys.copy()
        return False
    genimg_key = genai_keys_for_genimg.pop(0)
    #print_with_time(genimg_key)
    genimg_client = genai.Client(api_key=genimg_key)
    return True
pop_key_for_genimg()

cwd = os.getcwd()
scoped_dir = os.getenv("SCPDIR", os.path.join(cwd, "scoped_dir"))

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

print_with_time(cwd)

driver = None

def update():
    pass
def pickle_all():
    pass

try:
    # Initialize the driver
    driver = __chrome_driver__(scoped_dir, headless)
    actions = ActionChains(driver)
    start_shorturl_thread()

    tz_params = {'timezoneId': 'Asia/Ho_Chi_Minh'}
    driver.execute_cdp_cmd('Emulation.setTimezoneOverride', tz_params)
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

    c_user, i_user = None, None
    try:
        with open("logininfo.json", "r", encoding='utf-8') as f:
            login_info = json.load(f)
            onetimecode = login_info.get("onetimecode", "")
            work_jobs = parse_opts_string(login_info.get("work_jobs", "aichat,friends"))
            c_user = login_info.get("c_user", None)
            i_user = login_info.get("i_user", None)
    except Exception as e:
        onetimecode = ""
        work_jobs = parse_opts_string("aichat,friends")
        print_with_time(e)

    print_with_time("Danh sách jobs:", work_jobs)

    admin_fbid = work_jobs.get("aichat_adminfbid", "100013487195619")

    driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": True})
    driver.get("https://www.facebook.com/")
    driver.delete_all_cookies()
    for cookie in cookies:
        cookie.pop('expiry', None)  # Remove 'expiry' field if it exists
        driver.add_cookie(cookie)
    print_with_time("Đã khôi phục cookies")
    set_facebook_id(driver, c_user, i_user)
    cookies = driver.get_cookies()
    driver.execute_cdp_cmd("Emulation.setScriptExecutionDisabled", {"value": False})
    driver.get("https://www.facebook.com/me/photos_by/")
    wait_for_load(driver)
    
    # Define a mapping of chat tabs to their corresponding URLs
    def __init_last_reload_ts_mapping():
        return {
            chat_tab : 0,
            mobileview : 0,
        }
    last_reload_ts_mapping = __init_last_reload_ts_mapping()
    ee2e_resolved = False
    screenshot_ids_to_backup = set()

    def check_fb_login():
        global cookies, bak_cookies, last_reload_ts_mapping
        try:
            current_url = driver.current_url
            if is_facebook_domain(current_url) and get_path(current_url).startswith("/checkpoint/"):
                print_with_time("Tài khoản bị đình chỉ bởi Facebook")
                raise KeyboardInterrupt
            new_cookies = driver.get_cookies()
            if is_facebook_logged_out(new_cookies):
                if check_cookies_(cookies) == 1:
                    # The cookies is not actually die
                    print_with_time("Cập nhật lại cookies")
                    for cookie in cookies:
                        cookie.pop('expiry', None)  # Remove 'expiry' field if it exists
                        driver.add_cookie(cookie)
                    set_facebook_id(driver, c_user, i_user)
                    last_reload_ts_mapping = __init_last_reload_ts_mapping()
                    driver.get("https://www.facebook.com/me/photos_by/")
                    wait_for_load(driver)
                    time.sleep(1)
                elif bak_cookies is not None:
                    print_with_time("Tài khoản bị đăng xuất, sử dụng cookies dự phòng")
                    # TODO: obtain new cookies
                    driver.delete_all_cookies()
                    for cookie in bak_cookies:
                        cookie.pop('expiry', None)  # Remove 'expiry' field if it exists
                        driver.add_cookie(cookie)
                    set_facebook_id(driver, c_user, i_user)
                    bak_cookies = None
                    last_reload_ts_mapping = __init_last_reload_ts_mapping()
                    driver.get("https://www.facebook.com/me/photos_by/")
                    wait_for_load(driver)
                    time.sleep(1)
                else:
                    print_with_time("Tài khoản bị đăng xuất")
                    raise KeyboardInterrupt
        except Exception as e:
            print_with_time("Lỗi xảy ra:", e)
            pass # Ignore all errors
    # Double check
    check_fb_login()
    check_fb_login()

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
    chat_histories_prev_hash = hash_dict(chat_histories)

    self_facebook_info = pickle_from_file(f_self_facebook_info, { })
    
    sk_list = [
            "about_places",
            "about_contact_and_basic_info",
        ]
    self_url = get_facebook_profile_url(cookies)

    self_fbid = get_facebook_id(self_url)
    if self_fbid is None:
        self_fbid = get_facebook_id_from_cookies(cookies)
    print_with_time(f"URL là {self_url}")
    self_image_prompt = []

    photos = {}
    links = driver.find_elements(By.CSS_SELECTOR, 'a[role="link"]')
    for link in links:
        try:
            href = link.get_attribute("href")
            if get_path(href) == "/photo.php":
                images = link.find_elements(By.CSS_SELECTOR, "img")
                for image in images:
                    src = image.get_attribute("src")
                    src = register_shorturl(urljoin(driver.current_url, src))
                    alt = image.get_attribute("alt")
                    photos[src] = alt
        except Exception:
            pass
    def collect_photos():
        global self_image_prompt
        _tmp_prompt = []
        if photos:
            _tmp_prompt = ["Your photos that you uploaded on Facebook:"]
            for src, alt in photos.items():
                info_json = json.dumps({ "url" : src, "caption" : alt }, ensure_ascii=False)
                _tmp_prompt.append(info_json)
                image_bytes = download_file_to_bytesio(src)
                image = Image.open(image_bytes)
                _tmp_prompt.append(image)
            self_image_prompt = _tmp_prompt
    # Create and configure the thread as a daemon
    thread = threading.Thread(target=collect_photos)
    thread.daemon = True  # Set as daemon
    thread.start()

    if self_facebook_info.get("Facebook name", None) is None or self_facebook_info.get("Facebook id", "") != self_fbid:
        print_with_time("Đang đọc thông tin cá nhân...")
        wait_for_load(driver)

        myname = get_facebook_name("me", cookies)
        self_facebook_info = { "Facebook name" : myname, "Facebook id" : self_fbid, "Facebook url" :  self_url }
        pickle_to_file(f_self_facebook_info, self_facebook_info)
        if on_github_workflows:
            upload_file(GITHUB_TOKEN, GITHUB_REPO, f_self_facebook_info, STORAGE_BRANCE)
    self_facebook_info["Facebook photos"] = photos
    myname = self_facebook_info["Facebook name"]
    gemini_dev_mode = work_jobs.get("aichat", "normal") == "devmode"

    main_model_config = None
    safety_settings = [ # This must be a list of SafetySetting objects
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_NONE,
                )
            ]

    def load_instruction():
        global main_model_config
        if on_github_workflows:
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_intro_txt, STORAGE_BRANCE, f_intro_txt)
        with open(f_intro_txt, "r", encoding='utf-8') as f: # What kind of person will AI simulate?
            ai_prompt = f.read()
        # Setup overall guidance to the model
        instruction = get_instructions_prompt(myname, ai_prompt, self_facebook_info, gemini_dev_mode)
        main_model_config = {
            "system_instruction": instruction
        }

    load_instruction()

    def reply_generate_content(parts):
        return client.models.generate_content(
            model=GENAI_MODEL,
            contents=parts,
            config = GenerateContentConfig(
                system_instruction=main_model_config["system_instruction"],
                safety_settings=safety_settings,
                response_mime_type="application/json",
                tools=[google_search_tool],
            )
        )

    def summary_generate_content(parts):
        return client.models.generate_content(
            model=GENAI_MODEL,
            contents=parts,
            config = GenerateContentConfig(
                system_instruction=[ get_devmode_prompt(), "You are a summary model. When I give a prompt, your output must be a summary of the chat conversation, including all previous summaries and important context. Do not include quoted sentences, markdown, or formatting. The summary should be in English, direct, and retain essential details for future reference." ],
                safety_settings=safety_settings,
            )
        )

    # Facebook info
    f_facebook_infos = "facebook_infos.bin"
    try:
        if on_github_workflows:
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_facebook_infos, STORAGE_BRANCE, f_facebook_infos)
    except Exception as e:
        print_with_time(e)
    facebook_infos = pickle_from_file(f_facebook_infos, {})
    # Chat info
    f_chat_infos = "chat_infos.bin"
    try:
        if on_github_workflows:
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_chat_infos + ".enc", STORAGE_BRANCE, f_chat_infos + ".enc")
            decrypt_file(f_chat_infos + ".enc", f_chat_infos, encrypt_key)
    except Exception as e:
        print_with_time(e)
    chat_infos = pickle_from_file(f_chat_infos, {})
    def extract_names():
        result = {"self", "admin"}
        for value in chat_infos.values():
            name = value.get("idname")
            if name is not None:
                result.add(name)
        return result
    def find_info_by_name(name):
        for key, value in chat_infos.items():
            if value.get("idname") == name:
                return key, value
        return None, None  # if not found
    
    # Migrate from old to new list
    __old_status = chat_histories.pop("status", {})
    if __old_status:
        for key, val in __old_status.items():
            set_structure(chat_infos, [key])
            chat_infos[key] = { "chatable" : val }
    del __old_status
    set_structure(chat_infos, [admin_fbid, "admin_settings"])
    chat_infos[admin_fbid]["admin_settings"].setdefault("aichat", True)
    chat_infos[admin_fbid]["admin_settings"].setdefault("aichat_lite", False)
    chat_infos[admin_fbid]["admin_settings"].setdefault("aichat_xxx", False)
    chat_infos[admin_fbid]["admin_settings"].setdefault("genai_visual", True)
    chat_infos[admin_fbid]["admin_settings"].setdefault("auto_friends", "friends" in work_jobs)
    chat_infos[admin_fbid]["admin_settings"].setdefault("lang", "vi")
    global_set = {}
    

    def __set_rules(rules = None):
        if rules is None:
            rules = chat_infos[admin_fbid]["admin_settings"].setdefault("opts", "none")
        else:
            chat_infos[admin_fbid]["admin_settings"]["opts"] = rules
        try:
            global_set["rules"] = parse_opts_string(rules)
        except Exception:
            global_set["rules"] = {}
        global_set["reset_regex"] = global_set["rules"].get("resetat", None)
        global_set["reset_msg"] = global_set["rules"].get("resetmsg", None)
        global_set["stop_regex"] = global_set["rules"].get("stopat", None)
        global_set["stop_msg"] = global_set["rules"].get("stopmsg", None)
        global_set["start_regex"] = global_set["rules"].get("startat", None)
        global_set["start_msg"] = global_set["rules"].get("startmsg", None)
        global_set["bye_msg"] = global_set["rules"].get("byemsg", None)
    
    lang_maps = {
        "en" : 0,
        "vi" : 1,
    }
    def TL(list_text):
        lang = chat_infos[admin_fbid]["admin_settings"]["lang"]
        lang_num = lang_maps.get(lang, 0)
        if len(list_text) < lang_num +1:
            return list_text[0]
        return list_text[lang_num]
    

    __set_rules()

    ######################################
    print_with_time("Bắt đầu khởi động!")
    ######################################

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
                for msg in chat_history:
                    if msg["message_type"] == "file" and msg["info"]["url"] == None:
                        # Update url of file
                        msg["info"]["url"] = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{msg["info"]["file_name"]}'
        if os.path.exists("screenshot"):
            branch = upload_file(GITHUB_TOKEN, GITHUB_REPO, "screenshot", generate_hidden_branch())
            try:
                shutil.rmtree("screenshot") # Destroy directory after upload
            except Exception:
                pass # Ignore all error
            for msg_id in screenshot_ids_to_backup:
                chat_infos.setdefault(msg_id, {})["screenshot"] = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/screenshot/{msg_id}.png'
        # Backup chat_histories
        pickle_to_file(f_chat_infos + ".enc", chat_infos, encrypt_key)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_chat_infos + ".enc", STORAGE_BRANCE)
        pickle_to_file(f_chat_history + ".enc", chat_histories, encrypt_key)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_chat_history + ".enc", STORAGE_BRANCE)
        return True

    def pickle_all():
        global chat_histories_prev_hash
        if chat_histories_prev_hash == hash_dict(chat_histories):
            return False
        print_with_time("Xuất dữ liệu")
        chat_histories_prev_hash = hash_dict(chat_histories)
        pickle_to_file(f_facebook_infos, facebook_infos)
        pickle_to_file(f_chat_history, chat_histories)
        pickle_to_file(f_chat_infos, chat_infos)


    def get_message_input():
        btns = driver.find_elements(By.CSS_SELECTOR, 'div[role="textbox"] p')
        return btns[0] if len(btns) > 0 else None
    def get_alert():
        btns = driver.find_elements(By.CSS_SELECTOR, 'div[role="alert"]')
        return btns[0] if len(btns) > 0 else None

    fake_typing = False
    def do_fake_typing():
        global fake_typing
        while True:
            try:
                if fake_typing:
                    get_message_input().send_keys(" ")
            except Exception: pass
            time.sleep(2)
    # Create and configure the thread as a daemon
    thread = threading.Thread(target=do_fake_typing)
    thread.daemon = True  # Set as daemon
    thread.start()

    driver.switch_to.window(mobileview)
    driver.get("https://www.facebook.com/language/")
    switched_to_english = False
    last_reload_ts_mapping[mobileview] = 1

    while True:
        try:
            time.sleep(1)
            if not switched_to_english:
                if driver.current_window_handle != mobileview:
                    driver.switch_to.window(mobileview)
                english_buttons = []
                for element in driver.find_elements(By.CSS_SELECTOR, 'div[data-type="vscroller"] > div'):
                    if element.text == "English":
                        english_buttons.append(element)
                        break
                if len(english_buttons) > 0:
                    driver.execute_script("arguments[0].click();", english_buttons[0])
                    print_with_time("Switched to English")
                    switched_to_english = True
            elif chat_infos[admin_fbid]["admin_settings"].get("auto_friends", False):
                if last_reload_ts_mapping.get(mobileview, 0) == 0:
                    if driver.current_window_handle != mobileview:
                        driver.switch_to.window(mobileview)
                    last_reload_ts_mapping[mobileview] = 1
                    driver.get("https://m.facebook.com/")
                    wait_for_load(driver)
                elif (int(time.time()) - last_reload_ts_mapping.get(mobileview, 0)) > 60*30:
                    if driver.current_window_handle != mobileview:
                        driver.switch_to.window(mobileview)
                    last_reload_ts_mapping[mobileview] = int(time.time())
                    friend_tab_btn = driver.find_elements(By.XPATH, "//span[contains(text(), '󰎍') or contains(text(), '󱎍')]")
                    if len(friend_tab_btn) > 0:
                        driver.execute_script("arguments[0].click();", friend_tab_btn[0])
                        time.sleep(1)
                        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.loading-overlay")))
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

            if driver.current_window_handle != chat_tab:
                driver.switch_to.window(chat_tab)
            # AICHAT START
            if True:
                if last_reload_ts_mapping.get(chat_tab, 0) == 0:
                    print_with_time(f"Khởi động Messenger")
                    js_pushstate(driver, MESSENGER_HOME_PAGE)
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
                # find all chat buttons
                chat_btns = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/messages/"]')
                current_unix = int(time.time())
                for chat_btn in chat_btns:
                    try:
                        new_chat_indicator = chat_btn.find_elements(By.CSS_SELECTOR, 'div[role="button"][aria-hidden="true"]')
                        
                        href = chat_btn.get_attribute("href")
                        message_id = get_last_part(href)
                        chat_info = { "id" : message_id, "href" : href }
                        info = chat_infos.get(message_id, {})
                        
                        delay_rep_time = info.get("delaytime", None) is not None and (current_unix >= info.get("delaytime", current_unix))
                        
                        if not delay_rep_time and len(new_chat_indicator) <= 0 and ("no_welcome" in global_set["rules"] or chat_histories.get(message_id, None)):
                            continue
                        
                        in_cooldown = info.get("cooldown", None) is not None and (current_unix < info.get("cooldown", 0))
                        if in_cooldown:
                            continue
                        
                        if (chat_infos[admin_fbid]["admin_settings"].get("aichat", True) == False or info.get("block", False) == True) and info.get("fbid", message_id) != admin_fbid:
                            continue
                        chat_list.append(chat_info)
                    except Exception:
                        continue

                if len(chat_list) > 0:
                    print_with_time(f"Nhận được {len(chat_list)} tin nhắn mới")
                    for chat_info in chat_list:
                        if True:
                            is_group_chat = False
                            chat_href = chat_info["href"]
                            main = driver.find_elements(By.CSS_SELECTOR, 'div[role="main"]')
                            if len(main) > 0:
                                main = main[0]
                                driver.execute_async_script("""
                                    var callback = arguments[arguments.length - 1];  // Get the callback function
                                    window.__old_main = arguments[0]; // Keep in memory
                                    arguments[0].remove();  // Remove the element
                                    callback();  // Call the callback once done
                                """, main)
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
                                break
                            
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
                                        print_with_time(f"Đang lấy thông tin cá nhân từ {profile_link}")
                                        parsed_url = urlparse(profile_link)
                                        # Remove the trailing slash from the path, if it exists
                                        urlpath = parsed_url.path
                                        # Split the path and extract the ID
                                        facebook_id = get_last_part(urlpath)
                                        who_chatted = get_facebook_name(facebook_id, cookies)
                                        if not who_chatted:
                                            print_with_time(f"Không thể lấy thông tin")
                                            continue
                                        
                                        facebook_info = { 
                                            "Facebook name" : who_chatted,
                                            "Facebook url" :  profile_link,
                                            "Last access" : int(time.time())
                                        }
                                        
                                        facebook_infos[profile_link] = facebook_info
                                        js_pushstate(driver, chat_href)
                                    else:
                                        who_chatted = facebook_info.get("Facebook name")

                                    facebook_info["Last access"] = int(time.time())
                                else:
                                    is_group_chat = True
                                    group_name = main.find_elements(By.CSS_SELECTOR, "h2")
                                    who_chatted = group_name[0].text if len(group_name) > 0 else ""
                                    facebook_info = { "Facebook group name" : who_chatted, "Facebook url" :  driver.current_url }
                                # Parse and get id
                                parsed_url = urlparse(driver.current_url)
                                urlpath = parsed_url.path
                                message_id = get_last_part(urlpath)
                                if facebook_id is None:
                                    parsed_url = urlparse(facebook_info.get("Facebook url", None))
                                    urlpath = parsed_url.path
                                    facebook_id = get_last_part(urlpath)
                            except Exception as e:
                                print_with_time(e)
                                continue

                        print_with_time(f"Tin nhắn mới từ {who_chatted} (ID: {facebook_id})")
                        if "debug" in global_set["rules"]:
                            print_with_time(json.dumps(facebook_info, ensure_ascii=False, indent=2))
                        set_structure(chat_infos, [message_id])
                        chat_infos[message_id]["name"] = who_chatted
                        chat_infos[message_id]["fbid"] = facebook_id
                        if chat_infos[message_id].get("idname", None) is None:
                            chat_infos[message_id]["idname"] = nickname.generate(who_chatted, extract_names())
                        # Pop delaytime
                        delay_is_set = chat_infos[message_id].pop("delaytime", None) is not None
                        # Remove cooldown
                        chat_infos[message_id].pop("cooldown", 0)
                        caption = chat_info.pop("caption", None)

                        while True:
                            try:
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
                                        file_result = []
                                        final_last_msg = copy.deepcopy(msg)
                                        if msg["message_type"] == "text_message" and is_cmd(msg["info"]["msg"]):
                                            final_last_msg["info"]["msg"] = "<This is command message. It has been hidden>"
                                        if msg["message_type"] == "file":
                                            final_last_msg["info"]["loaded"] = msg["info"].get("loaded", False) and not chat_infos[admin_fbid]["admin_settings"].get("aichat_lite", False)
                                        if msg["message_type"] == "file" and final_last_msg["info"].get("loaded", False):
                                            file_name = msg["info"]["file_name"]
                                            mime_type = msg["info"]["mime_type"]
                                            file_upload = None
                                            if msg["info"].get("url", None) is None:
                                                final_last_msg["info"]["url"] = get_local_file_url(file_name) # Generate temp url
                                            else:
                                                final_last_msg["info"]["url"] = register_shorturl(final_last_msg["info"]["url"])
                                            try:
                                                # find the cached files first
                                                file_upload = client.files.get(name=file_name)
                                            except Exception:
                                                #traceback.print_exc()
                                                try:
                                                    # generate new file name if possible to avoid any conflict
                                                    file_name = f"files/{generate_random_string(40)}"
                                                    get_raw_file(final_last_msg["info"]["url"], file_name)
                                                    file_upload = client.files.upload(file = file_name, config = UploadFileConfig(mime_type=mime_type,name=file_name))
                                                    # update new name
                                                    msg["info"]["file_name"] = file_name
                                                except Exception as e:
                                                    file_result.append(f"{file_name} cannot be loaded. You might ask user to resend the file")
                                                    print_with_time(e)
                                                    #traceback.print_exc()
                                            if file_upload is not None:
                                                if file_upload.state == FileState.ACTIVE:
                                                    if msg["info"].get("last_state", None) != FileState.ACTIVE:
                                                        file_result.append(f"{file_name} is ready for you to view it!")
                                                    file_result.append(file_upload)
                                                elif file_upload.state == FileState.FAILED:
                                                    file_result.append(f"{file_name} cannot be loaded. You might ask user to resend the file")
                                                else:
                                                    file_result.append(f"{file_name} is being sent to you. Please wait a moment!")
                                                msg["info"]["last_state"] = file_upload.state
                                        result.append(json.dumps(final_last_msg, ensure_ascii=False))
                                        result.extend(file_result)
                                    return result

                                def release_unload_files(chat_history, do_all = False):
                                    result = []
                                    for msg in chat_history:
                                        if msg["message_type"] == "file" and (do_all or msg["info"].get("loaded", False) == False):
                                            try:
                                                file_name = msg["info"]["file_name"]
                                                client.files.delete(name=file_name)
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

                                print_with_time("Đang đọc tin nhắn...")

                                command_result = []
                                should_stop = False
                                should_not_chat = chat_infos.get(message_id, {}).get("chatable", True) == False or chat_infos.get(facebook_id, {}).get("chatable", True) == False
                                max_video = 10
                                num_video = 0
                                max_file = 10
                                num_file = 0
                                regex_rules_applied = global_set["rules"].get(f"{facebook_id}_rules", "")
                                regex_rules_applied = regex_rules_applied.split() if regex_rules_applied else []
                                reset_regex_list = { global_set["reset_regex"] : global_set["reset_msg"] }
                                stop_regex_list = { global_set["stop_regex"] : global_set["stop_msg"] }
                                start_regex_list = { global_set["start_regex"] : global_set["start_msg"] }
                                bye_msg_list = [ global_set["bye_msg"] ]
                                
                                if regex_rules_applied:
                                    print_with_time(f"Áp dụng quy tắc: {regex_rules_applied}")
                                    for name in regex_rules_applied:
                                        reset_regex = global_set["rules"].get(f"{name}_resetat", None)
                                        reset_msg = global_set["rules"].get(f"{name}_resetmsg", None)
                                        reset_regex_list[reset_regex] = reset_msg
                                        
                                        stop_regex = global_set["rules"].get(f"{name}_stopat", None)
                                        stop_msg = global_set["rules"].get(f"{name}_stopmsg", None)
                                        stop_regex_list[stop_regex] = stop_msg
                                        
                                        start_regex = global_set["rules"].get(f"{name}_startat", None)
                                        start_msg = global_set["rules"].get(f"{name}_startmsg", None)
                                        start_regex_list[start_regex] = start_msg
                                        
                                        bye_msg_list.append(global_set["rules"].get(f"{name}_byemsg", None))

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
                                    read_elements = []
                                    reading_time = get_day_and_time()
                                    for msg_element in reversed(msg_table.find_elements(By.CSS_SELECTOR, 'div[role="row"]')):
                                        try:
                                            checkpointed = msg_element.get_attribute("checkpoint")
                                        except Exception:
                                            checkpointed = "none"
                                        finally:
                                            if checkpointed == "checkpointed":
                                                break
                                            read_elements.append(msg_element)

                                        try:
                                            timedate = msg_element.find_element(By.CSS_SELECTOR, 'span[class="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1pg5gke xvq8zen xo1l8bm x12scifz"]')
                                            chat_history_new.insert(0, {"message_type" : "conversation_event", "info" : timedate.text})
                                        except Exception:
                                            pass

                                        # Finding name
                                        indicator = msg_element.find_elements(By.CSS_SELECTOR, 'div.x15zctf7')
                                        if len(indicator) > 0:
                                            break
                                        # Scrape user name
                                        name = None
                                        mark = "text_message"
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
                                            quotes_text = msg_element.find_element(By.CSS_SELECTOR, 'div.xi81zsa.x126k92a').text
                                            chat_history_new.insert(0, {"message_type" : "replied_to_message", "info" : {"name" : name, "mentioned_message" : quotes_text}, "reading_time" : reading_time})
                                        except Exception:
                                            pass

                                        try:
                                            msg_frame = msg_element.find_element(By.CSS_SELECTOR, 'div.html-div[dir="auto"]')
                                            msg = msg_frame.text
                                            mentioned_to_me = msg_frame.find_elements(By.CSS_SELECTOR, f'a[href="https://www.facebook.com/{self_fbid}/"]')
                                            if len(mentioned_to_me) > 0:
                                                chat_infos.setdefault(message_id, {})["chatable"] = True
                                                chat_infos.setdefault(facebook_id, {})["chatable"] = True
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
                                        
                                        image_elements = msg_element.find_elements(By.CSS_SELECTOR, 'img[src^="data:image/jpeg;base64,"]')
                                        image_elements.extend(msg_element.find_elements(By.CSS_SELECTOR, 'a[href^="/messenger_media/"] img'))
                                        image_elements.extend(msg_element.find_elements(By.CSS_SELECTOR, 'img.xz74otr.xmz0i5r.x193iq5w'))
                                        for image_element in image_elements:
                                            try:
                                                skip_check = image_element.get_attribute("skip_check")
                                                if skip_check == "1":
                                                    continue
                                                driver.execute_script("arguments[0].setAttribute('skip_check', '1')", image_element)
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
                                               
                                                chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send image", "file_name" : image_name, "mime_type" : "image/jpeg" , "url" : None, "loaded" : True }, "reading_time" : reading_time})
                                            except Exception:
                                                pass

                                        try:
                                            video_element = msg_element.find_element(By.CSS_SELECTOR, 'video')
                                            video_url = video_element.get_attribute("src")
                                            video_name = f"files/{generate_random_string(40)}"
                                            files_mapping[video_name] = ("url", video_url)

                                            chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send video", "file_name" : video_name, "mime_type" : "video/mp4", "url" : None, "loaded" : False }, "reading_time" : reading_time})
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

                                            chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send audio", "file_name" : audio_name, "mime_type" : "audio/mp4", "url" : None, "loaded" : True }, "reading_time" : reading_time})
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
                                                chat_history_new.insert(0, {"message_type" : "file", "info" : {"name" : name, "msg" : "send file", "file_name" : file_name, "mime_type" : mime_type, "url" : None, "loaded" : False }, "reading_time" : reading_time})
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
                                        
                                        chat_history_new.insert(0, {"message_type" : mark, "info" : {"name" : name, "msg" : msg}, "reading_time" : reading_time})
                                    for msg_element in read_elements:
                                        driver.execute_script("arguments[0].setAttribute('checkpoint', 'checkpointed')", msg_element)
                                    return chat_history_new, files_mapping

                                try: # Emulate typing...
                                    if not get_message_input():
                                        if get_alert():
                                            actions.move_to_element(get_alert()).click().perform()
                                        break
                                    actions.move_to_element(get_message_input()).click().perform()
                                    if not should_not_chat:
                                        actions.move_to_element(get_message_input()).click().send_keys(" ").perform()
                                except Exception:
                                    pass
                                chat_history_new, files_mapping = process_elements(msg_table)
                                print_with_time("Đã đọc xong!")
                                try: # save the screenshot
                                    os.makedirs("screenshot", exist_ok=True)
                                    main.screenshot(f"screenshot/{message_id}.png")
                                    screenshot_ids_to_backup.add(message_id)
                                except Exception:
                                    print_with_time("! Không thể lưu ảnh chụp màn hình")
                                
                                id_invalid_err = "ID must be numeric"

                                def reset_chat(chatid = None, title = None):
                                    """
                                    Clear chat history. 
                                    Make bot start with clean memory.
                                    /cmd reset <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    if title == None:
                                        title = "New chat"
                                    chat_histories[chatid] = [{"message_type" : "new_chat", "info" : title}]
                                    return TL([
                                        'I will forget everything in chat: {CHATID}',
                                        'Tôi sẽ quên mọi thứ trong chat: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))
                                        

                                def resetall(title = None, _1 = None):
                                    """
                                    Erase all chat histories.
                                    /cmd resetall
                                    """
                                    for key in chat_histories:
                                        reset_chat(key, title)
                                    return "Bot has been reset"

                                def mute_chat(mode, _1 = None):
                                    global should_not_chat
                                    if mode == "true" or mode == "1":
                                        chat_infos.setdefault(message_id, {})["chatable"] = False
                                        chat_infos.setdefault(facebook_id, {})["chatable"] = False
                                        should_not_chat = True
                                        return f'Bot has been muted'
                                    if mode == "false" or mode == "0":
                                        chat_infos.setdefault(message_id, {})["chatable"] = True
                                        chat_infos.setdefault(facebook_id, {})["chatable"] = True
                                        return f'Bot has been unmuted'
                                    return f'Unknown mute mode! Use "1" to mute the bot or "0" to unmute the bot.'


                                def set_litemode(mode, _1 = None):
                                    """
                                    Enable litemode to reduce input processing.
                                    It's useful if Gemini server is overloaded.
                                    But bot cannot view media such as photos, videos, ...
                                    /cmd lite [true|false]
                                    """
                                    if mode == None:
                                        mode = ""
                                    if mode.lower() == "true" or mode == "1":
                                        chat_infos[admin_fbid]["admin_settings"]["aichat_lite"] = True
                                        return TL([
                                            'Lite mode enabled',
                                            'Đã bật chế độ Lite'
                                        ])
                                    if mode.lower() == "false" or mode == "0":
                                        chat_infos[admin_fbid]["admin_settings"]["aichat_lite"] = False
                                        return TL([
                                            'Lite mode disabled',
                                            'Đã tắt chế độ Lite'
                                        ])
                                    return 'Lite mode: {MODE}'.format(MODE = chat_infos[admin_fbid]["admin_settings"].get("aichat_lite", False))

                                def set_autofriends(mode, _1 = None):
                                    """
                                    Enable or disable auto adding friends
                                    /cmd autofr [true|false]
                                    """
                                    if mode == None:
                                        mode = ""
                                    if mode.lower() == "true" or mode == "1":
                                        chat_infos[admin_fbid]["admin_settings"]["auto_friends"] = True
                                        return TL(['I will accept new friend requests', 'Tôi sẽ chấp nhận các lời mời kết bạn mới'])
                                    if mode.lower() == "false" or mode == "0":
                                        chat_infos[admin_fbid]["admin_settings"]["auto_friends"] = False
                                        return TL(['I will stop adding new friend requests', 'Tôi sẽ dừng chấp nhận các lời mời kết bạn mới'])
                                    return 'Auto friends: {MODE}'.format(MODE = chat_infos[admin_fbid]["admin_settings"].get("auto_friends", False))

                                def mute_by_id(chatid, _1 = None):
                                    """
                                    Mute bot in this chat.
                                    In group chat, unmute it by tagging its name.
                                    /cmd mute <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_infos.setdefault(chatid, {})["chatable"] = False
                                    return TL([
                                        'I will be silent in chat: {CHATID}',
                                        'Tôi sẽ tim lặng trong chat: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))

                                def unmute_by_id(chatid, _1 = None):
                                    """
                                    Unmute bot in this chat.
                                    /cmd unmute <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_infos.setdefault(chatid, {})["chatable"] = True
                                    return TL([
                                        'I will continue to talk in chat: {CHATID}',
                                        'Tôi sẽ tiếp tục nói chuyện trong chat: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))


                                def block_by_id(chatid, _1 = None):
                                    """
                                    Block this chat so that
                                    bot will ignore all messages from it.
                                    /cmd block <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_infos.setdefault(chatid, {})["block"] = True
                                    return TL([
                                        'Blocked: {CHATID}',
                                        'Đã chặn: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))


                                def unblock_by_id(chatid, _1 = None):
                                    """
                                    Unblock this chat so that
                                    bot will continue to interact with chat.
                                    /cmd unblock <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_infos.setdefault(chatid, {})["block"] = False
                                    return TL([
                                        'Unblocked: {CHATID}',
                                        'Đã bỏ chặn: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))


                                def allow_xxx(chatid, _1 = None):
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if chatid == "*":
                                        chat_infos[admin_fbid]["admin_settings"]["aichat_xxx"] = True
                                        return TL([
                                            'I am allowed to send xxx by default',
                                            'Tôi đã được phép gửi xxx theo mặc định'
                                        ])
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_infos.setdefault(chatid, {})["xxx"] = True
                                    return TL([
                                        'I am allowed to send xxx in chat: {CHATID}',
                                        'Tôi đã được phép gửi xxx trong chat: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))


                                def deny_xxx(chatid, _1 = None):
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if chatid == "*":
                                        chat_infos[admin_fbid]["admin_settings"]["aichat_xxx"] = False
                                        return TL([
                                            'I am deny from sending xxx by default',
                                            'Tôi bị cấm gửi xxx theo mặc định'
                                        ])
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_infos.setdefault(chatid, {})["xxx"] = False
                                    return TL([
                                        'I will no longer send xxx in chat: {CHATID}',
                                        'Tôi sẽ không còn gửi xxx trong chat: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))


                                def dump_chat(chatid, _1 = None):
                                    """
                                    Dump the chat that bot have saved into memory.
                                    /cmd dump <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    return pasterman(json.dumps(chat_histories.get(chatid, []), ensure_ascii=False, indent=2))

                                def checkib(chatids, msg=None):
                                    """
                                    Ask bot to check the chat given by id 
                                    /cmd checkib <id/idname>
                                    and send message if provided
                                    /cmd send <id/idname> <msg>
                                    """
                                    results = []
                                    for chatid in chatids.split(","):
                                        chatid = chatid.strip()
                                        result = checkib_single(chatid, msg)
                                        results.append(result)
                                    return "\n".join(results)

                                # Rename the original checkib to checkib_single to avoid naming conflict
                                def checkib_single(chatid, msg=None):
                                    if chatid is None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    chat_info = { "id": chatid, "href": f"/messages/t/{chatid}" }
                                    ok = TL([
                                        'I will check out the chat: {CHATID}',
                                        'Tôi sẽ đi kiểm tra chat: {CHATID}'
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))
                                    if msg is not None:
                                        chat_info["caption"] = json.dumps({"info": {"msg": msg}}, indent=4, ensure_ascii=False)
                                        ok = TL([
                                            'I will send to {CHATID}: {MSG}',
                                            'Tôi sẽ gửi tới {CHATID}: {MSG}'
                                        ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid), MSG = msg)
                                    chat_list.append(chat_info)
                                    return ok

                                def get_info(name, _1 = None):
                                    """
                                    Get infomation of bot.
                                    /cmd get [inbox|enckey|intro|info|rules|status|genkey]
                                    """
                                    if name == "inbox":
                                        # Return list of bot's inboxes
                                        text = "LIST:  \n"
                                        for key, val in chat_infos.items():
                                            text += (
                                                f"- ID:{key}\n"
                                                + (f"  IDNAME:{val.get('idname')}\n" if val.get('idname') is not None else "")
                                                + f"  FBID:{val.get('fbid', key)}\n"
                                                + f"  NAME:{val.get('name', 'Unknown')}\n"
                                                + f"  CHAT:{val.get('chatable', True)}\n"
                                                + f"  BLOCK:{val.get('block', False)}\n"
                                                + f"  XXX:{val.get('xxx', chat_infos[admin_fbid]['admin_settings']['aichat_xxx'])}\n"
                                                "\n"
                                            )
                                        return pasterman(text)
                                    if name == "cookies":
                                        # Return running cookies of bot
                                        return f'{selenium_cookies_to_cookie_header(cookies)}'
                                    if name == "bakcookies":
                                        # Return alternative cookies of bot
                                        return f'{selenium_cookies_to_cookie_header(bak_cookies)}'
                                    if name == "enckey":
                                        # Return encrypted key of encrypted files
                                        return PASSWORD
                                    if name == "intro":
                                        # Return AI's persona instruction
                                        return pasterman(ai_prompt)
                                    if name == "info":
                                        # Return bot's Facebook information
                                        return pasterman(json.dumps(self_facebook_info, ensure_ascii=False, indent=2))
                                    if name == "rules":
                                        # Return current setting rules
                                        return f'Rules: {chat_infos[admin_fbid]["admin_settings"].setdefault("opts", "")}'
                                    if name == "status":
                                        # Return status of bot, whenever it's running automated reply or not
                                        return f"""AICHAT:{chat_infos[admin_fbid]['admin_settings'].get('aichat')} LITE:{chat_infos[admin_fbid]["admin_settings"].get("aichat_lite", False)}"""
                                    if name == "genkey":
                                        # Return Gemini API Key
                                        return f'Gemini API KEY: {genai_keys_text}'
                                    return f"Invalid argument: {name}"

                                def terminate(_0 = None, _1 = None):
                                    """
                                    Terminate and shut down bot.
                                    You need to start bot manually after that!
                                    /cmd terminate
                                    """
                                    global should_stop
                                    should_stop = True
                                    return "Good bye!"

                                def do_stop(_0 = None, _1 = None):
                                    """
                                    Stop bot automated reply.
                                    /cmd stop
                                    """
                                    chat_infos[admin_fbid]["admin_settings"]["aichat"] = False
                                    return TL(['I will stop replying to anyone', 'Tôi sẽ dừng trả lời bất kỳ ai'])

                                def do_start(_0 = None, _1 = None):
                                    """
                                    Start bot automated reply.
                                    /cmd start
                                    """
                                    chat_infos[admin_fbid]["admin_settings"]["aichat"] = True
                                    return TL(['I will start replying to new message', 'Tôi sẽ bắt đầu trả lời tin nhắn mới'])

                                def update_model(_0 = None, _1 = None):
                                    """
                                    Update model with new instruction.
                                    /cmd update
                                    """
                                    load_instruction()
                                    return "Update model!"

                                def set_rules(rules, _1 = None):
                                    """
                                    Give bot the rules.
                                    /cmd setrules <id/oldidname> <idname>
                                    """
                                    if rules is not None:
                                        __set_rules(rules)
                                        return TL(["Rules have been set to {rules}", "Đã đặt quy tắc: {rules}"]).format(rules=rules)
                                    return TL(["Nothing to set?", "Không có gì để đặt à?"])

                                def getid(_0 = None, _1 = None):
                                    """
                                    Get Facebook ID of this chat.
                                    /cmd getid
                                    """
                                    return facebook_id

                                def get_screenshot(chatid, _1 = None):
                                    """
                                    Get screenshot of chat given by id.
                                    /cmd screenshot <id/idname>
                                    """
                                    if chatid == None or chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    screenshot_path = f"screenshot/{chatid}.png"
                                    if os.path.exists(screenshot_path):
                                        return open_file_in_bytesio(screenshot_path)
                                    info = chat_infos.get(chatid, {})
                                    backup = info.get("screenshot", None)
                                    if info.get("screenshot", None) is not None:
                                        os.makedirs("screenshot", exist_ok=True)
                                        download_file_to_path(backup, screenshot_path)
                                        if os.path.exists(screenshot_path):
                                            return open_file_in_bytesio(screenshot_path)
                                    return TL([
                                        (
                                            "No screenshot for {CHATID}\n"
                                            "Try check the inbox first by:\n"
                                                "/cmd checkib {CHATID}"
                                        ),
                                        (
                                            "Không có screenshot cho {CHATID}\n"
                                            "Bạn có thể yêu cầu tôi kiểm tra inbox:\n"
                                                "/cmd checkib {CHATID}"
                                        )
                                    ]).format(CHATID = chat_infos.get(chatid, {}).get('idname', chatid))
                                    

                                def setname(chatid, name_to_generate = None):
                                    """
                                    Give a chat a custom id name instead of numberic id.
                                    /cmd setname <id/oldidname> <idname>
                                    """
                                    if chatid == None:
                                        return TL(["Please provide a chat id!", "Hãy cung cấp một chat id"])
                                    if chatid == "self":
                                        chatid = message_id
                                    if not chatid.isnumeric():
                                        chatid, _ = find_info_by_name(chatid)
                                        if chatid == None:
                                            return id_invalid_err
                                    idname = nickname.generate(name_to_generate, extract_names())
                                    if name_to_generate == None:
                                        return TL(["Please provide a valid name!", "Hãy cung cấp một tên hợp lệ"])
                                    chat_infos.setdefault(chatid, {})["idname"] = idname
                                    return TL([
                                        "Set id name of {CHATID} to {idname}",
                                        "Đã đặt tên id cho {CHATID} thành {idname}"
                                    ]).format(CHATID = chatid, idname = idname)

                                def set_lang(lang, _1=None):
                                    """
                                    Set language for bot.
                                    /cmd lang [en|vi]
                                    """
                                    if lang == None:
                                        return TL(["English", "Tiếng Việt"])
                                    if lang not in lang_maps:
                                        return TL(["Invalid language to set", "Ngôn ngữ không hợp lệ"])
                                    chat_infos[admin_fbid]["admin_settings"]["lang"] = lang
                                    return TL(["Language has been set to English", "Ngôn ngữ đã đặt thành Tiếng Việt"])

                                def set_genai_visual(mode, _1=None):
                                    """
                                    Simulates the visual artifacts of a real phone camera capturing an image,
                                    in order to reduce the detectability of AI-generated images.
                                    /cmd genaivisual [true|false]
                                    """
                                    if mode == None:
                                        mode = ""
                                    if mode.lower() == "true" or mode == "1":
                                        chat_infos[admin_fbid]["admin_settings"]["genai_visual"] = True
                                        return TL([
                                            'I will simulate the visual phenomena of the camera for any AI generated image', 
                                            'Tôi sẽ mô phỏng các hiện tượng thị giác của máy ảnh cho các ảnh tạo ảnh bằng AI'
                                        ])
                                    if mode.lower() == "false" or mode == "0":
                                        chat_infos[admin_fbid]["admin_settings"]["genai_visual"] = False
                                        return TL([
                                            'I will not simulate anything after creating the image with AI', 
                                            'Tôi sẽ không mô phỏng bất cứ thứ gì sau khi tạo hình ảnh bằng AI'
                                        ])
                                    return 'GenAI Camera Visual: {MODE}'.format(MODE = chat_infos[admin_fbid]["admin_settings"].get("genai_visual", True))

                                def show_help(_0=None, _1=None):
                                    """
                                    Show detailed help for all available commands with descriptions.
                                    /cmd help
                                    """

                                    help_text = "Detailed Help for Available Commands:\n\n"

                                    for fn in set(func.values()):
                                        doc = fn.__doc__
                                        if doc:
                                            help_text += '\n'.join(line.strip() for line in doc.splitlines())

                                    help_text += "\nUser-level commands:\n\n"

                                    for fn in set(func_noadmin.values()):
                                        doc = fn.__doc__
                                        if doc:
                                            help_text += '\n'.join(line.strip() for line in doc.splitlines())

                                    return pasterman(help_text)

                                # Dictionary mapping arg1 to functions
                                func = {
                                    "reset": reset_chat,
                                    "mute" : mute_by_id,
                                    "unmute" : unmute_by_id,
                                    "get" : get_info,
                                    "dump" : dump_chat,
                                    "terminate" : terminate,
                                    "update" : update_model,
                                    "allowxxx" : allow_xxx,
                                    "denyxxx" : deny_xxx,
                                    "checkib" : checkib,
                                    "send" : checkib, #checkib and send are same
                                    "setrules" : set_rules,
                                    "stop" : do_stop,
                                    "start" : do_start,
                                    "resetall": resetall,
                                    "block" : block_by_id,
                                    "unblock" : unblock_by_id,
                                    "ss" : get_screenshot,
                                    "screenshot" : get_screenshot,
                                    "setname" : setname,
                                    "lite" : set_litemode,
                                    "autofr": set_autofriends,
                                    "help": show_help,
                                    "lang" : set_lang,
                                    "genaivisual" : set_genai_visual,
                                }
                                
                                func_noadmin = {
                                    "getid" : getid,
                                }

                                def parse_and_execute(command):
                                    # Parse the command
                                    args = shlex.split(command)
                                    
                                    # Check if the command starts with /cmd
                                    if len(args) < 2 or args[0] != "/cmd":
                                        return "Invalid command format. Use: /cmd arg1 arg2"
                                    
                                    # Extract arg1 and arg2
                                    arg1 = args[1]
                                    arg2 = args[2] if len(args) > 2 else None
                                    arg3 = args[3] if len(args) > 3 else None
                                    
                                    # Check if arg1 is in func and execute
                                    if arg1 in func:
                                        if facebook_id != admin_fbid:
                                            return "?"
                                        try:
                                            return func[arg1](arg2, arg3)
                                        except Exception as e:
                                            return f"Error while executing function: {e}"
                                    elif arg1 in func_noadmin:
                                        try:
                                            return func_noadmin[arg1](arg2, arg3)
                                        except Exception as e:
                                            return f"Error while executing function: {e}"
                                    else:
                                        return f"Unknown command: {arg1}"

                                if caption is None:
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
                                            (reset_regex_list, reset_chat, None),
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
                                            if isinstance(result, str):
                                                send_keys_long_text(driver, get_message_input(), result)
                                                get_message_input().send_keys("\n") # Press Enter to send
                                            elif isinstance(result, BytesIO):
                                                ext, mime_type = get_mine_type(result.name)
                                                drop_file(driver, get_message_input(), result, mime_type)
                                                get_message_input().send_keys("\n") # Press Enter to send
                                        if is_group_chat: chat_infos[message_id]["cooldown"] = int(time.time()) + 10
                                    del command_result
                                except Exception:
                                    pass
                                if should_stop:
                                    time.sleep(10)
                                    raise KeyboardInterrupt
                                is_command_msg = last_msg["message_type"] == "text_message" and is_cmd(last_msg["info"]["msg"])
                                is_file = last_msg["message_type"] == "file"
                                if caption is None:
                                    if is_command_msg:
                                        break
                                    if should_not_chat:
                                        break
                                    if not genai_keys:
                                        break
                                    if is_file and not delay_is_set:
                                        # Wait user to send text message in 30s before process
                                        chat_infos[message_id]["delaytime"] = int(time.time()) + 30
                                        break
                                fake_typing = True

                                for file_name, file_info in files_mapping.items():
                                    info_type = file_info[0]
                                    file_data = file_info[1] if info_type == "data" else (
                                        get_file_data(driver, file_info[1]) if file_info[1].startswith("blob:")
                                        else requests.get(file_info[1]).content
                                    )
                                    file_object = BytesIO(file_data)
                                    os.makedirs(os.path.dirname(file_name), exist_ok=True)
                                    bytesio_to_file(file_object, file_name)
                                    del file_data, file_object
                                del files_mapping

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
                                        response = summary_generate_content(prompt_to_summary)
                                        release_unload_files(chat_history[:summary_lines], True)
                                        summary = response.text
                                        if summary is None:
                                            raise Exception("Error summary")
                                        del chat_history[:-left_lines]
                                        chat_history.insert(0, {"message_type" : "summary_old_chat", "info" : summary})
                                    except Exception as e:
                                        print_with_time(f"Error summary: {e}")

                                chat_history_temp = chat_history.copy()
                                chat_history_temp.extend(chat_history_new)
                                for msg in reversed(chat_history_temp):
                                    if msg["message_type"] == "file":
                                        if msg["info"]["msg"] == "send video":
                                            num_video += 1  # Increment first
                                            msg["info"]["loaded"] = num_video <= max_video  # Compare after incrementing
                                        elif msg["info"]["msg"] == "send file":
                                            num_file += 1  # Increment first
                                            msg["info"]["loaded"] = num_file <= max_file  # Compare after incrementing
                                def build_prompt(chat_history):
                                    prompt_list = [f'The Messenger conversation with "{who_chatted}" is as json here:']
                                    prompt_list.extend(process_chat_history(chat_history))
                                    if chat_infos[admin_fbid]["admin_settings"].get("aichat_lite", False):
                                        prompt_list = [item for item in prompt_list if isinstance(item, str)]
                                        prompt_list.append("NOTE: You are in Lite mode, you cannot review media such as photos, sounds and videos now. Please notify users of this if they submit files.")
                                    if "debug" in global_set["rules"]:
                                        for prompt in prompt_list:
                                            print_with_time(prompt)
                                    print_with_time(f"<{len(chat_history_new)} tin nhắn mới từ {who_chatted}>")

                                    prompt_list.insert(0, header_prompt)
                                    if not chat_infos[admin_fbid]["admin_settings"].get("aichat_lite", False):
                                        prompt_list[:0] = self_image_prompt
                                    exam = json.dumps({"message_type" : "your_text_message", "info" : {"name" : myname, "msg" : "Your message is here"}}, indent = 4, ensure_ascii=False)
                                    prompt_list.append(f'>> Generate a response in properly formatted JSON to reply back to user. ABSOLUTELY NO phrases like: “Wait a minute,” “Looking for it,” “Take it easy,” “I’m looking it up,” “Let me check,” or any variation of waiting, looking, or checking. When you receive a question, you must respond immediately as if you already know the information. Do not appear to be processing or delaying. Do not repeat what you already asked or said again!\nExample:\n{exam}\n')
                                    return prompt_list
                                prompt_list = build_prompt(chat_history_temp)
                                
                                for _x in range(10):
                                    try:
                                        button = get_message_input()
                                        if button is None:
                                            break
                                        if caption is None:
                                            response = reply_generate_content(prompt_list)
                                            try:
                                                caption = response.text
                                            except Exception:
                                                pass
                                        if caption is None:
                                            chat_history_temp = [{"message_type" : "summary_old_chat", "info" : "The previous conversation has been deleted, so you will have to start from scratch. Please inform others that the old topic is no longer appropriate for conversation!"}]
                                            prompt_list = build_prompt(chat_history_temp)
                                            raise JSON5DecodeError("No content is generated") # Ask Gemini to re-generate JSON
                                        if caption is not None:
                                            img_search = {}
                                            json_msg = fix_json(caption)
                                            media_history = []
                                            try:
                                                original_msg = json_msg["info"]["msg"]
                                                reply_msg = original_msg
                                            except Exception:
                                                caption = None
                                                raise JSON5DecodeError("Error getting message") # Ask Gemini to re-generate JSON
                                            reply_msg, img_search["on"] = extract_keywords(r'\[img\](.*?)\[/img\]', reply_msg)
                                            reply_msg, _img_search = extract_keywords(r'\[image\](.*?)\[/image\]', reply_msg) # Backward compatible
                                            img_search["on"].extend(_img_search)
                                            if chat_infos.get(message_id, {}).get("xxx", chat_infos[admin_fbid]["admin_settings"]["aichat_xxx"]) == True:
                                                reply_msg, img_search["off"] = extract_keywords(r'\[adultimg\](.*?)\[/adultimg\]', reply_msg)
                                            else:
                                                reply_msg, _img_search = extract_keywords(r'\[adultimg\](.*?)\[/adultimg\]', reply_msg)
                                                img_search["on"].extend(_img_search)
                                            reply_msg, img_search["link"] = extract_keywords(r'\[imglink\](.*?)\[/imglink\]', reply_msg)
                                            reply_msg, gen_imgs = extract_keywords(r'\[genimg\](.*?)\[/genimg\]', reply_msg)
                                            reply_msg, itunes_keywords = extract_keywords(r'\[itunes\](.*?)\[/itunes\]', reply_msg)
                                            reply_msg, bot_commands = extract_keywords(r'\[cmd\](.*?)\[/cmd\]', reply_msg)
                                            

                                            for adult, img_keywords in img_search.items():
                                                for img_keyword in img_keywords:
                                                    try:
                                                        for _x in range(5):
                                                            try:
                                                                image_link = img_keyword if adult == "link" else get_random_image_link(img_keyword, 30, adult)
                                                                image_io = download_file_to_bytesio(image_link)
                                                            except Exception:
                                                                continue
                                                            if "debug" in global_set["rules"]:
                                                                print_with_time(f"AI gửi ảnh {img_keyword} từ: {image_link}")
                                                            drop_image(driver, button, image_io)
                                                            media_history.append({"message_type" : "file", "info" : {"name" : myname, "msg" : "send image", "file_name" : f"files/{generate_random_string(40)}", "mime_type" : "image/jpeg" , "url" : image_link, "loaded" : True }, "sending_time" : get_day_and_time() })
                                                            del image_io
                                                            break
                                                    except Exception:
                                                        print_with_time(f"Không thể gửi ảnh: {img_keyword}")
                                            for gen_img in gen_imgs:
                                                gen_img_items = gen_img.split('|')
                                                gen_img = gen_img_items.pop()
                                                gen_img_prompt = [gen_img]
                                                for link in gen_img_items:
                                                    try:
                                                        image_io = download_file_to_bytesio(link)
                                                        image = Image.open(image_io)
                                                        gen_img_prompt.insert(0, image)
                                                    except Exception as e:
                                                        #print_with_time(f"Lỗi: {e}")
                                                        continue
                                                while True:
                                                    try:
                                                        images, texts, feedback = generate_image(genimg_client, gen_img_prompt)
                                                        chat_history_temp.append({
                                                            "message_type": "generate_image_result",
                                                            "info": {
                                                                "prompt": gen_img,
                                                                "texts": texts,
                                                                "feedback": feedback,
                                                                "final_result": (
                                                                    "UNABLE TO GENERATE: This could be due to a missing prompt or a "
                                                                    "violation of image creation rules. Check 'texts' and 'feedback' for more information!"
                                                                    if len(images) <= 0
                                                                    else f"GENERATED: {len(images)}"
                                                                )
                                                            }
                                                        })
                                                        for image_io in images:
                                                            if "debug" in global_set["rules"]:
                                                                print_with_time(f"AI gửi ảnh {gen_img} từ Gemini tạo ảnh")
                                                            if chat_infos[admin_fbid]["admin_settings"].get("genai_visual", True):
                                                                image_io = simulate_camera_effect_bytesio(image_io)
                                                            drop_image(driver, button, image_io)
                                                            file_name = f"files/{generate_random_string(40)}"
                                                            file_ext, mime_type = get_mine_type(image_io.name)
                                                            bytesio_to_file(image_io, file_name)
                                                            media_history.append({"message_type" : "file", "info" : {"name" : myname, "msg" : "send image", "file_name" : file_name, "mime_type" : mime_type , "url" : None, "loaded" : True }, "sending_time" : get_day_and_time() })
                                                            del image_io, file_name, file_ext, mime_type
                                                        del gen_img_prompt, images
                                                        break
                                                    except (ClientError, ServerError):
                                                        if pop_key_for_genimg(): # Try to switch key
                                                            continue
                                                        chat_history_temp.append({"message_type" : "generate_image_result", "info" : {"prompt" : gen_img, "final_result" : "FAILED TO GENERATED: ResourceExhausted"}})
                                                        break
                                                    except Exception as e:
                                                        print_with_time(f"Không thể gửi ảnh: {gen_img}")
                                                        chat_history_temp.append({"message_type" : "generate_image_result", "info" : {"prompt" : gen_img, "final_result" : "FAILED TO GENERATED"}})
                                                        #print_with_time(e)
                                                        break
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
                                                        if "debug" in global_set["rules"]:
                                                            print_with_time(f"AI gửi nhạc {itunes_keyword} từ: {itunes_link}")
                                                        drop_file(driver, button, music_io, "audio/mp4")
                                                        del music_ios
                                                        break
                                                except Exception:
                                                    print_with_time(f"Không thể gửi nhạc: {itunes_keyword}")
                                            if is_only_whitespace(reply_msg):
                                                reply_msg = "OK" + reply_msg
                                            print_with_time("* AI Trả lời:", reply_msg if "debug" in global_set["rules"] else "<1 tin nhắn>")
                                            fake_typing = False
                                            driver.execute_script("arguments[0].click();", button)
                                            button.send_keys(Keys.CONTROL + "a")  # Select all text
                                            button.send_keys(Keys.DELETE)  # Delete the selected text
                                            send_keys_long_text(driver, button, reply_msg)
                                            # There maybe newer msg while AI process chat
                                            chat_history_new, files_mapping = process_elements(msg_table)
                                            # Press Enter to send message
                                            button.send_keys("\n")
                                            if "bye" in bot_commands:
                                                print_with_time("* Bot yêu cầu dừng trả lời tin nhắn")
                                                chat_history_temp.append({"message_type" : "conversation_event", "info" : "You have left the conversation"})
                                                if is_group_chat and "aichat_nobye" not in global_set["rules"]:
                                                    chat_infos.setdefault(message_id, {})["chatable"] = False
                                                    chat_infos.setdefault(facebook_id, {})["chatable"] = False
                                                for bye_msg in bye_msg_list:
                                                    if bye_msg:
                                                        send_keys_long_text(driver, button, bye_msg)
                                                        button.send_keys("\n")
                                            try: # save the screenshot
                                                os.makedirs("screenshot", exist_ok=True)
                                                main.screenshot(f"screenshot/{message_id}.png")
                                            except Exception:
                                                print_with_time("! Không thể lưu ảnh chụp màn hình")
                                            chat_history_temp.extend(chat_history_new)
                                            chat_history_temp.extend(media_history)
                                            chat_history_temp.append({"message_type" : "your_text_message", "info" : {"name" : myname, "msg" : original_msg}, "sending_time" : get_day_and_time() })
                                            chat_histories[message_id] = chat_history_temp
                                            for file_name, file_info in files_mapping.items():
                                                info_type = file_info[0]
                                                file_data = file_info[1] if info_type == "data" else (
                                                    get_file_data(driver, file_info[1]) if file_info[1].startswith("blob:")
                                                    else requests.get(file_info[1]).content
                                                )
                                                file_object = BytesIO(file_data)
                                                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                                                bytesio_to_file(file_object, file_name)
                                                del file_object, file_data
                                            del files_mapping
                                            if is_group_chat: chat_infos[message_id]["cooldown"] = int(time.time()) + 10
                                        break
                                    except NoSuchElementException:
                                        print_with_time("Không thể trả lời")
                                        break
                                    except (ClientError, ServerError) as e:
                                        if pop_key_for_genai(): # Switch key if possible
                                            chat_list.append(chat_info)
                                        print_with_time(e)
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
                                    fake_typing = True
                                    time.sleep(2)
                                break
                            except StaleElementReferenceException:
                                pass
                            except Exception as e:
                                print_with_time(e)
                                break
                            finally:
                                fake_typing = False
                    # Back to home
                    js_pushstate(driver, MESSENGER_HOME_PAGE)
            # AICHAT END
            
        except Exception as e:
            print_with_time(e)
        
        check_fb_login()
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
    if driver is not None:
        if on_github_workflows:
            update()
        else:
            pickle_all()
        print_with_time("Quit...")
        driver.quit()
    print_with_time("Done!")
    
