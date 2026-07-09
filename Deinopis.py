import WebCrawler as wc
import GSReadAndWrite as io
import GSParser as parser
import os
import json

# TODO: Set to automatically grab code from email
# TODO: Organize results
# TODO: Apply results directly to Google Sheets (?)
# TODO: Make headless once finished debugging


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    players = []
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = load_config(config_path)
    while True:
        option = input("Do you want to test login, sheets, quit?: ")
        if option == "login":
            wc.login(config)
        elif option == "sheets":
            players = parser.parse_players(io.read_songs_sheet(config))
            for player in players:
                print(f"{player.name}")
                for song in player.songs:
                    print(f"  {song.name} {song.votes_total}")
        elif option == "quit":
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()