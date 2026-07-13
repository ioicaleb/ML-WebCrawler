
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
import imaplib, email, shutil, time, re, os

code = ""

def wait_click(driver, locator, timeout=10):
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()

def fill_email(driver, locator, value, timeout=10):
    elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    elem.send_keys(value)

def fill_code(driver, locator, value, timeout=60):
    elems = WebDriverWait(driver, timeout).until(EC.visibility_of_all_elements_located(locator))
    for elem, digit in zip(elems, value):
        elem.send_keys(digit)

def click_by_text(driver, texts, timeout=10):
    for text in texts:
        try:
            xpath = (
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                "'abcdefghijklmnopqrstuvwxyz'), '{}')]"
                "|//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                "'abcdefghijklmnopqrstuvwxyz'), '{}')]"
                "|//input[@value='{}']"
            ).format(text.lower(), text.lower(), text)
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            ).click()
            return True
        except TimeoutException:
            continue
    return False

def get_spotify_code(config):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    time.sleep(15)
    mail.login(config.get("email"), config.get("password"))
    mail.select("inbox", readonly = False)
    waiting = True
    while waiting:
        status, messages = mail.search(None, '(FROM "Spotify")')   
        if status != 'OK' or not messages[0]:
            print("Email not found")
        else:
            break   
    email_id = messages[0].split()[-1]
    status, data = mail.fetch(email_id, "(RFC822)")
    if status != "OK":
        print("Subject not found")
        return
    msg = email.message_from_bytes(data[0][1])
    subject, encoding = email.header.decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding or "utf-8")
    match = re.search(r"\d{6}", subject)
    global code
    if match:
        code = match.group(0)
    if code:        
        mail.store(email_id, "+FLAGS", "\\Deleted")
        mail.expunge()
    mail.close()
    mail.logout()
    

def login(driver, config):
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options, service=Service(executable_path=config.get("executable_path")))
    login_url = config.get("league_url")
    driver.get(login_url)
    time.sleep(2)
    click_by_text(driver, ["spotify"])
    if "spotify.com" not in driver.current_url.lower():
        for locator in [
            (By.CSS_SELECTOR, "a[href*='spotify']"),
            (By.CSS_SELECTOR, "button[href*='spotify']"),
            (By.XPATH, "//button[contains(., 'Spotify')]"),
            (By.XPATH, "//a[contains(., 'Spotify')]"),
        ]:
            try:
                wait_click(driver, locator)
                break
            except TimeoutException:
                print("Can't get to Spotify")
                continue
    spotify_username = config.get("email")
    if not spotify_username:
        raise ValueError("Config file must contain email")
    for locator in [
        (By.ID, "username"),
        (By.CSS_SELECTOR, "input[id='username']"),
        (By.CSS_SELECTOR, "input[type='text']"),
    ]:
        try:
            fill_email(driver, locator, spotify_username)
            click_by_text(driver, "Continue")
            break
        except TimeoutException:
            print("Can't add email address")
            continue
    global code
    for locator in [
        (By.CSS_SELECTOR, "input[inputmode='numeric']"),
    ]:
        try:
            while code == "":
                get_spotify_code(config)
            fill_code(driver, locator, code)
            break
        except TimeoutException:
            continue
    code = ""
    for text in ["agree", "accept", "allow", "authorize"]:
        try:
            wait_click(
                driver,
                (
                    By.XPATH,
                    f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                    f"'abcdefghijklmnopqrstuvwxyz'), '{text}')]",
                ),
            )
            break
        except TimeoutException:
            continue
    WebDriverWait(driver, 10).until(
        lambda d: "app.musicleague.com" in d.current_url.lower() or "musicleague" in d.current_url.lower()
    )
    time.sleep(3)
    return driver

def use_previous_login(profile_src, config):
    driver = None
    profile_temp = "/tmp/ffx_crawler"
    try:
        if profile_src:
            if os.path.exists(profile_temp):
                try:
                    shutil.rmtree(profile_temp)
                except PermissionError:
                    os.rename(profile_temp, f"{profile_temp}_old_{int(time.time())}")
            ignore_files = shutil.ignore_patterns(
                "lock", ".parentlock", "parent.lock", 
                "sessionstore.jsonlz4", "compatibility.ini"
            )
            shutil.copytree(profile_src, profile_temp, ignore=ignore_files)
            options = Options()
            options.add_argument("-profile")
            options.add_argument(profile_temp)
            options.add_argument("-headless")
            driver = webdriver.Firefox(options=options, service=Service(executable_path=config.get("executable_path")))
            driver.get(config.get("league_url"))
            time.sleep(3)
            driver.refresh()
            if "invite" in driver.current_url or "login" in driver.current_url:
                raise RuntimeError(f"Previous login failed")
        print("Successfully used previous login")
    except Exception as e:
        print(f"An error occurred during login: {e}")
        return None
    return driver
