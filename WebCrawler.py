import time, imaplib, email, re, os, shutil, sys, json
from bs4 import BeautifulSoup, NavigableString
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from Objects import Round, Voter, Song, Player, convert_username_to_name
from SheetManager import get_defunct_players as gdp

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

def get_round_results(driver, config):
    active_players = config.get("username-player_name")
    defunct_players = get_defunct_players(config)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        round_card = soup.find_all(class_= "card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
        title = round_card.find("h5").get_text()
        description = round_card.find("p").get_text()
    except Exception as e:
        print(e)
        print("Can't get round information")    
    divs = soup.select("[id*='spotify']")
    submissions = []
    for div in divs:
        try:
            song_card = div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(2)")
            votes = int(div.select_one("div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > h3").get_text().strip())
            song_name = song_card.find().get_text().strip()
            username_div = div.select_one("div[class*='rank-'] > :first-child > :first-child > :last-child > h6")
            player_name = convert_username_to_name(active_players = active_players, defunct_players = defunct_players, name = song_name, username = username_div.get_text().strip())
            artist = song_card.select_one(":nth-child(2)").get_text().strip()
            album = song_card.select_one(":nth-child(3)").get_text().strip()
            voters=[]
            voters_card = div.select("[id*='votes'] > *")
            for voter_info in voters_card:
                voter_name = convert_username_to_name(active_players = active_players, username = voter_info.select_one(":nth-child(2) > b").get_text())
                vote_block = voter_info.select_one(":nth-child(3) > h6")
                if vote_block:
                    votes_total = int(vote_block.get_text().split()[0])
                else:
                    votes_total = 0
                comment = ""
                if voter_info.find("span"):
                    comment = voter_info.select_one(":nth-child(2) > span").get_text()
                voters.append(Voter(voter_name, votes_total, comment))
            submissions.append(Song(player_name=player_name, name=song_name, artist=artist, album=album, voters=voters, votes=votes))
        except Exception as e:
                print(e)
                print(f"Can't get submission information: p:{player_name}, s:{song_name}, ar:{artist}, al:{album}, vn: {voter_name}, vt: {votes_total}")
    return Round(title=title, round_number=round_number, description=description, submissions=submissions)

def get_all_rounds(driver, config):
    rounds = []
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data']))
    links = []
    for elem in elems:
        anchors = [anchor.get('href') for anchor in elem.find_all("a", href = True)]
        links.append(f"https://app.musicleague.com{anchors[2]}")
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        rounds.append(round)
    rounds.sort(key = lambda x: (x.round_number))
    return rounds 

def check_for_new_rounds(round_number, config):
    driver = get_driver(config)
    rounds_list = driver.current_url
    recent_round = get_recent_round_number(driver)
    missing_rounds = recent_round - round_number
    if missing_rounds > 0:
        driver.get(rounds_list)
        print(f"Getting information for {missing_rounds} rounds")
        rounds = get_missing_rounds(driver, config, missing_rounds)
        rounds = export_rounds(rounds)
        return bool(rounds)
    else:
        print("No new rounds")
        return False

def get_recent_round_number(driver):
    round_number = 0
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elem = soup.find('div', attrs = {'x-data': status_pattern})
    anchors = [anchor.get('href') for anchor in elem.find_all("a", href = True)]
    link = (f"https://app.musicleague.com{anchors[2]}")
    driver.get(link)
    time.sleep(1)
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and element.strip() == "":
                element.extract()
        round_card = soup.find_all(class_= "card")[5]
        round_number = int(round_card.find("span").get_text().split()[1])
    except Exception as e:
        print(e)
    return round_number

def get_missing_rounds(driver, config, missing_rounds):  
    with open("rounds.json", 'r') as f:
            rounds = json.load(f)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    status_pattern = re.compile(r"status:\s*'COMPLETE'")
    elems = soup.find_all(
        lambda tag: tag.name == 'div' and 
        tag.has_attr('x-data') and 
        status_pattern.search(tag['x-data']))
    links = []
    for i in range(missing_rounds):
        anchors = [anchor.get('href') for anchor in elems[i].find_all("a", href = True)]
        links.append(f"https://app.musicleague.com{anchors[2]}")
    for link in links:
        driver.get(link)
        time.sleep(1)
        round = get_round_results(driver, config)
        rounds.append(round)
    rounds.sort(key = lambda x: (x.round_number))
    return rounds

def get_defunct_players(config):
    cache_file = "defunct_players.json"
    players = []
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            players = json.load(f)
    if not players:
        players = gdp(config)
        with open(cache_file, 'w') as f:
            json.dump(players, f)
    return players

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

def export_players(rounds):
    players = []
    for round in rounds:
        for song in round.submissions:
            player = None
            if not any(player.name == song.player_name for player in players):
                player = Player(name=song.player_name, votes_to=0)
                player.wins = 0
                players.append(player)
            else:
                player = next((player for player in players if player.name == song.player_name), None)
            if player:
                player.votes_to += song.votes
        for name in round.winner:
            winner = next((player for player in players if player.name == name), None)
            if winner:
                winner.wins += 1
    players = sorted([vars(player) for player in players], key = lambda x: x["name"])
    with open("players.json", "w", encoding="utf-8") as json_file:
            json.dump(players, json_file, ensure_ascii=False, indent=4)
    return players


def export_songs(rounds):
    all_songs = []
    for round in rounds:
        songs = []
        song_number = 1
        for song in round.submissions:
            song.voters = [vars(voter) for voter in song.voters]
            all_songs.append(song)
            song.id = F"{song.player_name[:3].lower()}{song_number:02d}{round.round_number:02d}"
            songs.append(song.id)
            song_number += 1
    songs = sorted([vars(song) for song in all_songs], key = lambda x: (x["player_name"], -x["votes"]))
    with open("songs.json", "w", encoding="utf-8") as json_file:
            json.dump(songs, json_file, ensure_ascii=False, indent=4)
    return songs

def export_rounds(rounds):
    results = []
    for round in rounds:
        songs = []
        song_number = 1
        for song in round.submissions:
            song.id = F"{song.player_name[:3].lower()}{song_number}{round.round_number:02d}"
            songs.append(song.id)
            song_number += 1
        if songs:
            round.submissions = songs
        results.append(round.__dict__)
    with open("rounds.json", "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)    
    export_players(rounds)
    export_songs(rounds)
    return results

def get_results(config):
    driver = get_driver(config)
    if not driver:
        driver = webdriver.Firefox(service=Service(executable_path=config.get("executable_path")))
        login(driver, config)
    if driver:
        rounds = get_all_rounds(driver, config)
        results = export_rounds(rounds)
        driver.quit()
        return results
    print("Couldn't get results")

def get_driver(config):
    profile_src = config.get("ffx_profile_path")
    machine_type = os.environ.get("COMPUTER_TYPE", "desktop")
    if machine_type  == "laptop":
        profile_src += config.get("laptop_profile")
    else:
        profile_src += config.get("desktop_profile")
    driver = use_previous_login(profile_src, config)
    return driver
    