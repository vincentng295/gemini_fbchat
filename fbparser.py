import re
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

def is_facebook_profile_url(url):
    # Define the regex pattern
    pattern = r'^https?://(www\.)?facebook\.com/profile\.php\?id=[^&]+'
    # Check if the URL matches the pattern
    return re.match(pattern, url) is not None

def get_facebook_id(fburl, selenium_cookies = None):
    session = requests.Session()
    cookies = {cookie["name"]: cookie["value"] for cookie in selenium_cookies} if selenium_cookies else None
    source = session.get(fburl, cookies=cookies)
    soup = BeautifulSoup(source.text, 'html.parser')
    myid = soup.find('meta', {'property': 'al:android:url'})
    if myid != None:
        myid = myid['content']
    if myid != None:
        myid = myid.lstrip("fb://profile/")
    if myid == None:
        if is_facebook_profile_url(fburl):
            parsed_url = urlparse(fburl)
            query_params = parse_qs(parsed_url.query)
            myid = query_params.get('id', [None])[0]
    return myid

def get_facebook_profile_url(selenium_cookies):
    """Fetch the Facebook profile URL using cookies from cookies.json."""
    try:
        # Convert list format to dictionary for requests
        cookies = {cookie["name"]: cookie["value"] for cookie in selenium_cookies}
        # Send request to Facebook profile page
        response = requests.head("https://www.facebook.com/profile.php", cookies=cookies, allow_redirects=True)
        # Return the final URL (after any redirections)
        return response.url
    except Exception as e:
        return f"Error: {e}"

def get_facebook_name(fbid, selenium_cookies=None):
    import requests
    session = requests.Session()
    cookies = {cookie["name"]: cookie["value"] for cookie in selenium_cookies} if selenium_cookies else None
    fburl = f"https://www.facebook.com/{fbid}/?sk=about"
    response = session.get(fburl, cookies=cookies, allow_redirects=True)
    if response.status_code != 200 or fburl == response.url:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    title_tag = soup.find('title')
    return title_tag.text

def parse_facebook_username(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")   # bỏ dấu /
    return path.split("/")[0] if path else ""

def get_facebook_username(fblink, selenium_cookies=None):
    import requests
    cookies = {cookie["name"]: cookie["value"] for cookie in selenium_cookies} if selenium_cookies else None
    # check if it is Facebook link
    if not re.match(r'^https?://(www\.)?facebook\.com/.*', fblink):
            return None
    response = requests.head(fblink, cookies=cookies, allow_redirects=True)
    return parse_facebook_username(response.url)

def selenium_to_cookiejar(driver):
    jar = requests.cookies.RequestsCookieJar()
    for c in driver.get_cookies():
        jar.set(
            c['name'],
            c['value'],
            domain=c.get('domain'),
            path=c.get('path')
        )
    return jar

def build_headers(referer="https://facebook.com"):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer,
        "Origin": "https://facebook.com",
        "Connection": "keep-alive"
    }

def fb_get(url, cookies, referer="https://facebook.com"):
    try:
        res = requests.get(
            url,
            headers=build_headers(referer),
            cookies=cookies,
            timeout=10
        )
        return res.json()
    except:
        return None

def get_fb_list_image_link(driver, token):
    cookies = selenium_to_cookiejar(driver)
    url = f"https://graph.facebook.com/v18.0/me/photos?type=uploaded&fields=images,link,source&access_token={token}"
    links = []
    page_count = 0
    MAX_PAGES = 5
    while url and page_count < MAX_PAGES:
        data = fb_get(url, cookies)
        if not data or "data" not in data:
            break
        for p in data["data"]:
            images = p.get("images")
            if images and len(images) > 0:
                src = images[0].get("source")
                if src:
                    links.append(src)
        url = data.get("paging", {}).get("next")
        page_count += 1
    return links

def get_fb_avater_link(driver, token):
    cookies = selenium_to_cookiejar(driver)
    url = f"https://graph.facebook.com/v18.0/me/picture?redirect=false&width=1024&height=1024&access_token={token}"
    data = fb_get(url, cookies)
    if data:
        return data.get("data", {}).get("url")
    return None


def check_fb_username(driver, username, token):
    cookies = selenium_to_cookiejar(driver)
    url = f"https://graph.facebook.com/v18.0/{username}?access_token={token}"
    data = fb_get(url, cookies)
    if data and data.get("id") and data.get("name"):
        return data
    return None

def get_facebook_posts(driver, username, token):
    cookies = selenium_to_cookiejar(driver)
    info = check_fb_username(driver, username, token)
    if not info:
        return None, None
    url = f"https://graph.facebook.com/v18.0/{username}/posts?fields=message,created_time,full_picture&access_token={token}"
    data = fb_get(url, cookies)
    if data:
        return info, data.get("data")
    return info, None

def call_facebook_get_api(driver, endpoint, query, token):
    cookies = selenium_to_cookiejar(driver)
    if query:
        query += "&access_token=" + token
    else:
        query = "access_token=" + token
    query = query.replace("#", "%23").replace("?", "%3F")
    endpoint = endpoint.replace("#", "%23").replace("?", "%3F")
    url = f"https://graph.facebook.com/{endpoint}?{query}"
    return fb_get(url, cookies)
    