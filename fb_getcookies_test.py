from fb_getcookies import get_fb_cookies, check_cookies, parse_cookies
import os
import sys
import json
import time
from pickle_utils import *
from github_utils import *
from cryptography.fernet import Fernet

sys.stdout.reconfigure(encoding='utf-8')

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Pass GitHub Token
GITHUB_REPO = os.getenv("GITHUB_REPO")   # Pass the repository (owner/repo)
STORAGE_BRANCE = os.getenv("STORAGE_BRANCE")
if_running_on_github_workflows = (STORAGE_BRANCE is not None and STORAGE_BRANCE != "")
PASSWORD = os.getenv("PASSWORD")
encrypt_key = generate_fernet_key(PASSWORD)

f_login_info = "logininfo.json"
f_intro_txt = "setup/introduction.txt"
f_rules_txt = "setup/rules.txt"

cookies_text = None
alt_cookies_text = None
use_backup = True
ai_prompt = None

# Get the path to the event payload file
event_path = os.getenv('GITHUB_EVENT_PATH')

if event_path:
    # Read the event data from the file
    with open(event_path, 'r', encoding='utf-8') as f:
        event_data = json.load(f)

    # Extract the inputs from the event payload
    # Example for workflow_dispatch input
    login_info = event_data.get('inputs', {})

    cookies_text = login_info.get("cookies_text", None)
    login_info["cookies_text"] = None
    alt_cookies_text = login_info.get("alt_cookies_text", None)
    login_info["alt_cookies_text"] = None
    ai_prompt = login_info.get("ai_prompt", None)
    login_info["ai_prompt"] = None

    if login_info.get("username", None):
        with open(f_login_info, "w") as f:
            json.dump(login_info, f)
        use_backup = False

if use_backup:
    if if_running_on_github_workflows:
        try:
            # Download the encrypted file
            print(f"Đang khôi phục thông tin đăng nhập từ branch: {STORAGE_BRANCE}")
            get_file(GITHUB_TOKEN, GITHUB_REPO, f_login_info + ".enc", STORAGE_BRANCE, f_login_info + ".enc")
            print("Đang giải mã tập tin...")
            decrypt_file(f_login_info + ".enc", f_login_info, encrypt_key)
            print("Đã giải mã file thành công!")
        except Exception as e:
            print(e)

    with open(f_login_info, "r", encoding='utf-8') as f:
        login_info = json.load(f)

if ai_prompt is not None and ai_prompt != "":
    with open(f_intro_txt, "w", encoding='utf-8') as f: # What kind of person will AI simulate?
        f.write(ai_prompt)
    if if_running_on_github_workflows:
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_intro_txt, STORAGE_BRANCE, f_intro_txt)

if if_running_on_github_workflows:
    try:
        get_file(GITHUB_TOKEN, GITHUB_REPO, f_intro_txt, STORAGE_BRANCE, f_intro_txt)
    except Exception:
        # Else using default one
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_intro_txt, STORAGE_BRANCE, f_intro_txt)

username = login_info.get("username", None)
password = login_info.get("password", None)
otp_secret = login_info.get("otp_secret", "")
alt_account = login_info.get("alt_account", "0")

if alt_account == None or alt_account == "":
    alt_account = 0
else:
    alt_account = int(alt_account)

filename = "cookies.json"
bakfilename = "cookies_bak.json"
need_upload = False

try:
    if cookies_text is not None:
        with open(filename, "w") as cookies_file:
            json.dump(parse_cookies(cookies_text), cookies_file)
        need_upload = True
    elif if_running_on_github_workflows:
        # Download the encrypted file
        print(f"Đang khôi phục cookies từ branch: {STORAGE_BRANCE}")
        get_file(GITHUB_TOKEN, GITHUB_REPO, filename + ".enc", STORAGE_BRANCE, filename + ".enc")
        print("Đang giải mã tập tin...")
        decrypt_file(filename + ".enc", filename, encrypt_key)
        print("Đã giải mã file thành công!")
except Exception as e:
    print(e)

try:
    if alt_cookies_text is not None:
        with open(bakfilename, "w") as cookies_file:
            json.dump(parse_cookies(alt_cookies_text), cookies_file)
        need_upload = True
    elif if_running_on_github_workflows:
        # Download the encrypted file
        print(f"Đang khôi phục cookies từ branch: {STORAGE_BRANCE}")
        get_file(GITHUB_TOKEN, GITHUB_REPO, bakfilename + ".enc", STORAGE_BRANCE, bakfilename + ".enc")
        print("Đang giải mã tập tin...")
        decrypt_file(bakfilename + ".enc", bakfilename, encrypt_key)
        print("Đã giải mã file thành công!")
except Exception as e:
    print(e)

print("Kiểm tra cookies")
ret_cookies, cookies = check_cookies(filename)
print("Kiểm tra cookies dự phòng")
ret_bakcookies, bakcookies = check_cookies(bakfilename)

if ret_cookies == -1 or ret_bakcookies == -1:
    print("Tài khoản đã bị khóa")
    raise Exception("Facebook Login Exception")

if ret_cookies == 0:
    print("Cookies đã hết hạn sử dụng, sử dụng cookies dự phòng")
    cookies = bakcookies if ret_bakcookies == 1 else None
    ret_cookies = ret_bakcookies
    ret_bakcookies, bakcookies = 0, None

if username:
    for i in range(5):
        if ret_cookies == 0:
            print("Đang lấy cookies mới...")
            need_upload = True
            ret_cookies, cookies = get_fb_cookies(username, password, otp_secret, alt_account, incognito = True)
        if ret_cookies == -1:
            print("Tài khoản đã bị khóa")
            raise Exception("Facebook Login Exception")
        if cookies == None:
            time.sleep(5)
            continue
        break
    if cookies == None:
        print("Đăng nhập thất bại")
        raise Exception("Facebook Login Exception")
    for i in range(5):
        if ret_bakcookies == 0:
            print("Đang lấy cookies dự phòng mới...")
            need_upload = True
            ret_bakcookies, bakcookies = get_fb_cookies(username, password, otp_secret, alt_account, incognito = True)
        if ret_bakcookies == -1:
            print("Tài khoản đã bị khóa")
            raise Exception("Facebook Login Exception")
        if bakcookies == None:
            time.sleep(5)
            continue
        break

# Swap cookies to reduce the chance of cookies being logged out
with open(filename, "w") as cookies_file:
    json.dump(bakcookies, cookies_file)
with open(bakfilename, "w") as bakcookies_file:
    json.dump(cookies, bakcookies_file)

try:
    if if_running_on_github_workflows and need_upload:
        # Encrypt file with encrypt key
        print("Đang mã hóa tập tin trước khi tải lên...")
        encrypt_file(filename, filename + ".enc", encrypt_key)
        encrypt_file(bakfilename, bakfilename + ".enc", encrypt_key)
        encrypt_file(f_login_info, f_login_info + ".enc", encrypt_key)
        print("Mã hóa thành công!")
        # Upload the file onto repo
        upload_file(GITHUB_TOKEN, GITHUB_REPO, filename + ".enc", STORAGE_BRANCE)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, bakfilename + ".enc", STORAGE_BRANCE)
        upload_file(GITHUB_TOKEN, GITHUB_REPO, f_login_info + ".enc", STORAGE_BRANCE)
        print(f"Đã tải tệp lên branch: {STORAGE_BRANCE}")
except Exception as e:
    print(e)


