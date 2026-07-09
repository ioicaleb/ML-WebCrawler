from Objects import *
from selenium.webdriver.common.by import By

def parse_players(values):
    players = []

    if not values:
        print("No data found.")
        return

    i = 0
    while i < len(values[0]):
        player = Player()
        j = 0
        for row in values:
            j += 1
            if i >= len(row) or not row[i]:
                break
            if j == 1:
                player.name = row[i]
                continue
            if (i + 1) >= len(row) or not row[i + 1]:
                break
            if j == 2:
                continue
            
            song = Song(row[i], int(row[i + 1]), player.name)
            player.songs.append(song)

        if player.name is not None:
            player.songs.sort(key=lambda x: (x.votes), reverse=True)
            players.append(player)

        i += 2
    return players

###
def parse_songs(values):
    songs = []

    if not values:
        print("No data found.")
        return

    for row in values[1:]:
        if len(row) < 2:
            continue
        name = row[0]
        votes_total = int(row[1]) if row[1].isdigit() else 0
        song = Song(name, votes_total)
        songs.append(song)

    return songs

def parse_voters(voters_card):
    voters = []
    for vote_card in voters_card:
        voter = Voter(
            name = vote_card.find_element(By.CSS_SELECTOR, ":nth-child(2) > b").text,
            votes = int(vote_card.find_elements(By.CSS_SELECTOR, ":nth-child(3) > h6").text.split()[0]),
            comment = vote_card.find_elements(By.CSS_SELECTOR, ":nth-child(2) > span").text
            )
        voters.append(voter)
    return voters

def parse_submission(div, song_card, voters_card):
    song = Song(
        player_name = div.find_element(By.CSS_SELECTOR, "[id*='spotify']:nth-child(1) > :nth-child(2) > :nth-child(1) > :nth-child(1) > :last-child > h6").text,
        name = song_card.find_element(By.CSS_SELECTOR, ":nth-child(1)").text,
        artist = song_card.find_element(By.CSS_SELECTOR, ":nth-child(2)").text,
        album = song_card.find_element(By.CSS_SELECTOR, ":nth-child(3)").text,
        votes = int(div.find_element(By.CSS_SELECTOR, ":nth-child(1) > :nth-child(1) > :nth-child(3) > :nth-child(1)").text),
    )
    song.voters = parse_voters(voters_card)
    return song
        
def parse_round_results(title, round_number, description, results):
    return Round(title, round_number, description, results)

def merge_results(players, rounds):
    for round in rounds:
        for submission in round.submissions:
            for player in players:
                if player.name == submission.player_name:
                    for song in player.songs:
                        if song.name == submission.name:
                            song.votes = submission.votes
                            song.voters = submission.voters
                            break
                    break
    return players