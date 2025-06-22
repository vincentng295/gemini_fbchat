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
    script = """
    const scripts = document.querySelectorAll('script[type="application/json"]');
    const profileSwitcherProfiles = [];

    scripts.forEach((script) => {
      try {
        const json = JSON.parse(script.textContent);

        const nodes =
          json?.require?.[0]?.[3]?.[0]?.__bbox?.require?.[0]?.[3]?.[1]?.__bbox
            ?.result?.data?.viewer?.actor?.profile_switcher_eligible_profiles
            ?.nodes;

        if (nodes && Array.isArray(nodes)) {
          profileSwitcherProfiles.push(...nodes.map(n => n.profile.id));
        }
      } catch (e) {
        // skip errors
      }
    });

    return profileSwitcherProfiles;
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
