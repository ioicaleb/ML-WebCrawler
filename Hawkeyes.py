from WebCrawler import get_results, check_for_new_rounds
from SheetManager import post_player_sheet
import os
import json
import sys

# TODO: VOTE MATRIX
# TODO: Statistical analysis
# TODO: Only pull new data and append json files

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = load_config(config_path)
    results = None
    songs = None
    players = None
    if os.path.exists("rounds.json"):
        with open("rounds.json", 'r') as f:
            results = json.load(f)
    if results:
        print("Pulled previous results")
    else:
        results = get_results(config)
        if results:
            print("Results successfully obtained")
        else:
            print("Crawl failed")
            sys.quit()
    if os.path.exists("songs.json"):
        with open("songs.json", 'r') as f:
            songs = json.load(f)
    if os.path.exists("players.json"):
        with open("players.json", 'r') as f:
            players = json.load(f)
    if songs and players:
        last_round_number = results[-1]["round_number"]
        if check_for_new_rounds(last_round_number, config):
            if os.path.exists("songs.json"):
                with open("songs.json", 'r') as f:
                    songs = json.load(f)
            if os.path.exists("players.json"):
                with open("players.json", 'r') as f:
                    players = json.load(f)
        post_player_sheet(config, players, songs)
        print("Stat sheet updated successfully")
    elif not songs:
        print("Failed to get songs cache")
    else:
        print("Failed to get players cache")

if __name__ == "__main__":
    main()