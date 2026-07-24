"""
web_crawler.py - Web scraping module for Music League data

This module handles the scraping of Music League round data from the web,
including round information, song submissions, and voting details.
"""

import time
import re
from bs4 import BeautifulSoup, NavigableString
from data_collection.objects import Round, Voter, Song, convert_username_to_name
from data_collection.export_manager import export_rounds
from data_processing.cache_manager import read_json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# IN-MEMORY APP CACHE FOR RENDER LIFECYCLE
# Replaces local file persistence with database-synchronized runtime lookups
_global_avatar_cache = {}

def load_avatar_cache(database_avatars: dict):
    """Called by your pipeline step to synchronize your Postgres records with runtime memory."""
    global _global_avatar_cache
    _global_avatar_cache = database_avatars if database_avatars else {}

def get_avatar_cache() -> dict:
    """Returns the updated avatar records to be written into the Postgres JSONB schema."""
    global _global_avatar_cache
    return _global_avatar_cache

def get_driver(config):
    """
    Launches clean, container-ready headless WebDrivers matching the admin's selection profile.
    """
    browser_type = config.get("browser_type", "chromium")
    print(f"Container launching standard driver format: {browser_type}")

    if browser_type == "firefox":
        ff_options = FirefoxOptions()
        ff_options.add_argument("--headless")
        ff_options.add_argument("--no-sandbox")
        ff_options.add_argument("--disable-dev-shm-usage")
        return webdriver.Firefox(options=ff_options)
    else:
        # Default deployment: Chromium
        chrome_options = ChromeOptions()
        chrome_options.add_argument("--headless=new") 
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.binary_location = "/usr/bin/chromium"
        return webdriver.Chrome(options=chrome_options)

def get_avatar_url(div, player_name):
    """
    Extracts avatar image URL and updates an in-memory cache dictionary 
    instead of calling disk-bound write_json().
    """
    global _global_avatar_cache
    try:
        avatar_img = div.select_one("div[class*='rank-'] > :first-child > :first-child > :nth-child(2) > img")
        if not avatar_img:
            return
            
        avatar_url = avatar_img.get("src")
        _global_avatar_cache[player_name] = avatar_url
    except Exception as e:
        print(f"Failed parsing avatar for player {player_name}: {e}")

def get_round_results(driver, config):
    """
    Extract round information from a single round page.
    """
    players = config.get("username-player_name")
    
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup.find_all(string=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        
        round_card = soup.find_all(class_="card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
        title = round_card.find("h5").get_text()
        description = round_card.find("p").get_text()
        
    except Exception as e:
        print(f"Error getting round information: {e}")
        return None
    
    divs = soup.select("[id*='spotify']")
    submissions = []
    
    for div in divs:
        try:
            song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
            votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
            song_name = song_card.find().get_text().strip()
            
            username_div = div.select_one("div[class*='rank-'] > :first-child > :first-child > :last-child > h6")
            player_name = convert_username_to_name(
                username=username_div.get_text().strip(),
                players=players
            )
        
            # FIXED: Calling get_avatar_url matching its corrected operational state
            get_avatar_url(div, player_name)
            
            artist = song_card.select_one(":nth-child(2)").get_text().strip()
            album = song_card.select_one(":nth-child(3)").get_text().strip()
            
            voters = []
            voters_card = div.select("[id*='votes'] > *")
            
            for voter_info in voters_card:
                voter_name = convert_username_to_name(
                    username=voter_info.select_one(":nth-child(2) > b").get_text(),
                    players=players
                )
                
                vote_block = voter_info.select_one(":nth-child(3) > h6")
                votes_total = int(vote_block.get_text().split()[0]) if vote_block else 0
                
                comment = ""
                if voter_info.find("span"):
                    comment = voter_info.select_one(":nth-child(2) > span").get_text()
                
                voters.append(Voter(voter_name, votes_total, comment))
            
            submissions.append(Song(
                name=song_name,
                votes=votes,
                player_name=player_name,
                artist=artist,
                album=album,
                voters=voters
            ))
            
        except Exception as e:
            print(f"Error processing submission: {e}")
    
    return Round(title=title, round_number=round_number, description=description, submissions=submissions)

def get_all_rounds(driver, config):
    """
    Retrieve all completed rounds from the main page.
    """
    rounds = []
    time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
        if len(anchors) >= 3:
            links.append(f"https://app.musicleague.com{anchors[2]}")
    
    # FIXED: Re-attached the missing round extraction iteration loops
    for link in links:
        driver.get(link)
        time.sleep(1)
        round_data = get_round_results(driver, config)
        if round_data:
            rounds.append(round_data)
            
    rounds.sort(key=lambda x: x.round_number)
    return rounds

def check_for_new_rounds(round_number, config, existing_rounds_cache=None):
    """
    Check for and retrieve new rounds since the last known round in the database.
    """
    driver = get_driver(config)
    if not driver:
        print("Failed to get driver")
        return existing_rounds_cache if existing_rounds_cache else []
        
    try:
        # Inject cookie token to authenticate headless container
        driver.get("https://app.musicleague.com")
        driver.add_cookie({
            "name": "musicleague_user_session",
            "value": config.get("session_cookie"),
            "domain": ".musicleague.com",
            "path": "/"
        })
        
        driver.get(f"https://musicleague.com{config.get('league_id')}")
        rounds_list = driver.current_url
        recent_round = get_recent_round_number(driver)
        missing_rounds = recent_round - round_number
        
        if missing_rounds > 0:
            driver.get(rounds_list)
            print(f"Getting information for {missing_rounds} missing rounds")
            updated_rounds = get_missing_rounds(driver, config, missing_rounds, existing_rounds_cache)
            return updated_rounds
        else:
            print("No new rounds detected.")
            return existing_rounds_cache
    finally:
        driver.quit()

def get_recent_round_number(driver):
    """
    Get the most recent round number from the current page.
    """
    round_number = 0
    time.sleep(2)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        status_pattern = re.compile(r"status:\s*'COMPLETE'")
        elem = soup.find('div', attrs={'x-data': status_pattern})
        
        if elem:
            anchors = [anchor.get('href') for anchor in elem.find_all("a", href=True)]
            if len(anchors) >= 3:
                link = f"https://app.musicleague.com{anchors[2]}"
                driver.get(link)
                time.sleep(1)
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                for element in soup.find_all(string=True):
                    if isinstance(element, NavigableString) and element.strip() == "":
                        element.extract()
                
                round_card = soup.find_all(class_="card")[5]
                round_number = int(round_card.find("span").get_text().split()[1])
    except Exception as e:
        print(f"Error getting recent round number: {e}")
    return round_number

def get_missing_rounds(driver, config, missing_rounds, existing_rounds_cache):
    """
    Get specific missing rounds using state arrays injected from Postgres.
    """
    rounds = existing_rounds_cache if existing_rounds_cache else []
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data'])
    )
    
    links = []
    for i in range(min(missing_rounds, len(elems))):
        anchors = [anchor.get('href') for anchor in elems[i].find_all("a", href=True)]
        if len(anchors) >= 3:
            links.append(f"https://app.musicleague.com{anchors[2]}")
            
    for link in links:
        driver.get(link)
        time.sleep(1)
        round_data = get_round_results(driver, config)
        if round_data:
            rounds.append(round_data)
            
    rounds.sort(key=lambda x: x.round_number)
    return rounds

def get_results(config):
    """Main function to retrieve all round results during fallback setup initialization."""
    driver = get_driver(config)
    if not driver:
        return []
        
    try:
        driver.get("https://app.musicleague.com")
        driver.add_cookie({
            "name": "musicleague_user_session",
            "value": config.get("session_cookie"),
            "domain": ".musicleague.com",
            "path": "/"
        })
        
        driver.get(f"https://musicleague.com{config.get('league_id')}")
        rounds = get_all_rounds(driver, config)
        results = export_rounds(rounds, _global_avatar_cache)
        return results
    finally:
        driver.quit()