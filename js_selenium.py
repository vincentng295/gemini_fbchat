def js_sends_key(driver, e, content):
    driver.execute_async_script("""
    var e = arguments[0];
    var strings = arguments[1];
    var callback = arguments[2]; // Selenium's built-in async callback

    var index = 0;

    function typeCharacter() {
        if (index >= strings.length) {
            callback(); // ✅ Notify Selenium that execution is complete
            return;
        }

        var char = strings[index++];
        e.focus(); // Ensure the element is focused
        if (char === "\\n") { // Handle Enter key
            ["keydown", "keypress", "keyup"].forEach(function(eventType) {
                var event = new KeyboardEvent(eventType, {
                    key: "Enter",
                    code: "Enter",
                    keyCode: 13,
                    bubbles: true
                });
                e.dispatchEvent(event);
            });
        } else {
            document.execCommand("insertText", false, char);
            e.dispatchEvent(new Event("input", { bubbles: true }));
            e.dispatchEvent(new Event("change", { bubbles: true }));
        }

        // Simulate typing delay
        setTimeout(typeCharacter, Math.random() * 100 + 50);
    }

    typeCharacter(); // Start typing process
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