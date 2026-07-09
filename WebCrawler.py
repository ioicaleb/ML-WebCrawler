import time
import imaplib
import email
import re

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from Parser import parse_round_results, parse_submission

code = ""  # Global variable to store the Spotify verification code

def wait_click(driver, locator, timeout=10):
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator)).click()


def fill_email(driver, locator, value, timeout=10):
    elem = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    elem.send_keys(value)

def fill_code(driver, locator, value, timeout=10):
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
    status, msg_data = mail.fetch(email_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT)])")

    if status != "OK":
        print("Subject not found")
        return
    
    for data in msg_data:
        if isinstance(data, tuple):
            msg = email.message_from_bytes(data[1])
            raw_subject = msg["Subject"]

            decoded_parts = email.header.decode_header(raw_subject)
            subject = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    encoding = encoding or "utf-8"
                    subject = part.decode(encoding, errors="replace")
                else:
                    subject += part

            global code
            code = subject.split()[0]
    if code:        
        mail.store(email_id, "+FLAGS", "\\Deleted")
        mail.expunge()
    mail.close()
    mail.logout()
    

def login(driver, config):
    login_url = config.get("league_url")
    driver.get(login_url)

    # Click the Music League login option that redirects to Spotify
    click_by_text(driver, ["spotify"])

    # Try a few common Spotify login button/link selectors if the first attempt fails
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
                continue

    # Spotify login page
    spotify_username = config.get("email")
    
    if not spotify_username:
        raise ValueError("Config file must contain email")

    # Fill username
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
            continue

    global code
    # Fill code
    for locator in [
        (By.CSS_SELECTOR, "div[data-testid='phonelogin-code'] > input"),
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

    # Handle Spotify consent/authorization if it appears
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

    # Wait for redirect back to Music League
    WebDriverWait(driver, 45).until(
        lambda d: "app.musicleague.com" in d.current_url.lower() or "musicleague" in d.current_url.lower()
    )
    time.sleep(3)

    return driver

def get_round_results(driver):
    rounds = []
    #Get all completed rounds and open them in new tabs to get the results
    elems = WebDriverWait(driver, 45).until(EC.visibility_of_all_elements_located((By.XPATH, "//*[@x-data and contains(translate(@x-data, ' ', ''), \"status:'COMPLETE'\")]")))
    links = []
    for elem in elems:
        anchors = elem.find_elements(By.TAG_NAME, "a")
        link = anchors[2].get_attribute("href")
        links.append(link)

        round_list = driver.current_window_handle
    for link in links:
        # Open each completed round in a new tab to get the results and switch back to round list
        driver.switch_to.new_window('tab')
        driver.get(link)
        time.sleep(1)
        try:
            round_card = driver.find_elements(By.CSS_SELECTOR, "div.px-2:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1)")[1]
            round_number = round_card.find_element(By.CSS_SELECTOR, "span").text
            title = round_card.find_element(By.TAG_NAME, "h5").text
            description = round_card.find_element(By.TAG_NAME, "p").text
        except Exception as e:
            print(e)

        for locator in [
            (By.CSS_SELECTOR, "[id*='spotify']"),
        ]:
            try:
                divs = WebDriverWait(driver, 15).until(EC.visibility_of_all_elements_located(locator))
                results = []
                for div in divs:
                    try:
                        song_card = div.find_element(By.CSS_SELECTOR, ":nth-child(1) > :nth-child(1) > :nth-child(2)")
                        voters_card = div.find_element(By.CSS_SELECTOR, "[id*='votes']")
                        results.append(parse_submission(div, song_card, voters_card))
                    except Exception as e:
                        print(e)
            except TimeoutException:
                continue
            round = parse_round_results(title, round_number, description, results)
        rounds.append(round)
        driver.switch_to.window(round_list)
    return rounds.sort(key = lambda x: (x.round_number))

def crawl(config):
    driver = webdriver.Firefox(service=Service(executable_path=config.get("executable_path")))
    try:
        login(driver, config)
        results = get_round_results(driver)
        return results
    except Exception as e:
        print(f"An error occurred during login: {e}")
    return