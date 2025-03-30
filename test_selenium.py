from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fb_getcookies import __chrome_driver__
import time
import os

try:
    drivers = []
    scoped_dir = os.getenv("SCPDIR")
    print(scoped_dir)
    for opt in [
        (scoped_dir, False, True),
    ]:
        driver = __chrome_driver__(*opt)
        drivers.append(driver)
except Exception as e:
    print(e)
finally:
    for driver in drivers:
        driver.close()
        driver.quit()
