def js_input(driver, e, content):
    driver.execute_async_script("""
    var e = arguments[0];
    var strings = arguments[1];
    var callback = arguments[2]; // Selenium's built-in async callback

    e.focus();
    document.execCommand("insertText", false, strings);
    e.dispatchEvent(new Event("input", { bubbles: true }));
    e.dispatchEvent(new Event('change', { bubbles: true }));

    callback();
    """, e, content)


def js_type_input(driver, e, value):
    driver.execute_async_script("""
        var e = arguments[0];
        var strings = arguments[1];
        var callback = arguments[2]; // Selenium's built-in async callback
        e.setAttribute("type","hidden");
        e.setAttribute("value", strings);
        callback();
    """, e, value)

def js_pushstate(driver, path):
    driver.execute_async_script("""
        history.pushState({}, '', arguments[0]);
        window.dispatchEvent(new PopStateEvent('popstate'));
        var callback = arguments[1]; // Selenium's built-in async callback
        callback();
    """, path);

def inject_my_stealth_script(driver):
    stealth_script = """
    // Pass the WebDriver check
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    // Mimic a regular user's language settings
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    """
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": stealth_script}
    )

def get_profile_switcher_ids(driver):
    # --- Inject JS to extract profile IDs ---
    script = r"""
function findFirstViewerActorId(obj) {
  if (!obj || typeof obj !== "object") return null;
  if (obj.viewer && obj.viewer.actor && obj.viewer.actor.id) {
    return obj.viewer.actor.id;
  }
  for (const key in obj) {
    const val = obj[key];
    if (val && typeof val === "object") {
      const found = findFirstViewerActorId(val);
      if (found) return found;
    }
  }
  return null;
}

function findProfileSwitcherIds(obj, results = []) {
  if (!obj || typeof obj !== "object") return results;
  const ps = obj.profile_switcher_eligible_profiles;
  if (ps && Array.isArray(ps.nodes)) {
    ps.nodes.forEach(n => {
      const id = n && n.profile && n.profile.id;
      if (id) results.push(id);
    });
  }
  for (const key in obj) {
    const val = obj[key];
    if (val && typeof val === "object") {
      findProfileSwitcherIds(val, results);
    }
  }
  return results;
}

const scripts = document.querySelectorAll('script[type="application/json"]');
let mainUid = null;
const profileSwitcherProfiles = [];

scripts.forEach((script) => {
  try {
    const json = JSON.parse(script.textContent);
    if (!mainUid) {
      mainUid = findFirstViewerActorId(json);
    }
    profileSwitcherProfiles.push(...findProfileSwitcherIds(json));
  } catch (e) {
    // skip invalid JSON
  }
});

const ordered = [];
if (mainUid) ordered.push(mainUid);
profileSwitcherProfiles.forEach(id => {
  if (id && id !== mainUid) ordered.push(id);
});

const numericOnly = ordered.filter(id => typeof id === "string" && /^\d+$/.test(id));

const uniqueProfiles = [...new Set(numericOnly)];

return uniqueProfiles;
    """

    # --- Execute script and get the result ---
    profile_ids = driver.execute_script(script)
    return profile_ids

def js_click_at_center(driver, element):
    driver.execute_script("""
        function clickAtElementCenter(el) {
            const rect = el.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;

            const options = {
                bubbles: true,
                cancelable: true,
                view: window,
                clientX: x,
                clientY: y
            };

            el.dispatchEvent(new MouseEvent('mousedown', options));
            el.dispatchEvent(new MouseEvent('mouseup', options));
            el.dispatchEvent(new MouseEvent('click', options));
        }

        clickAtElementCenter(arguments[0]);
    """, element)

  
def get_fb_list_image_link(driver, token):
    script = """
    const callback = arguments[arguments.length - 1];
    const token = arguments[0];

    async function getAllPhotos() {
        let url = `https://graph.facebook.com/v18.0/me/photos?type=uploaded&fields=images,link,source&access_token=${token}`;
        let links = [];

        while (url) {
            const res = await fetch(url, {
                method: "GET",
                mode: "cors",
                credentials: "include",
                referrer: "https://facebook.com"
            });

            const json = await res.json();

            if (!json.data) break;

            const pageLinks = json.data
                .map(p => p.images && p.images[0] && p.images[0].source)
                .filter(Boolean);

            links.push(...pageLinks);

            url = json.paging && json.paging.next
                ? json.paging.next
                : null;
        }

        return links;
    }

    getAllPhotos().then(callback).catch(e => callback([]));
    """

    return driver.execute_async_script(script, token)

  
