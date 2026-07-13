from Objects import Player
from JSONManager import *

def get_song(song_id):
    songs = read_json("songs")
    song_list =[song for song in songs if song['id'] == song_id]
    if song_list:
        return song_list[0]
    print(f"Could not find song with id {song_id}") 

def export_players(rounds):
    players = []
    for round in rounds:
        if not isinstance(round, dict):
            round = round.__dict__
        for song in round["submissions"]:
            if isinstance(song, str):
                song = get_song(song)
            if not isinstance(song, dict):
                song = song.__dict__
            player = Player(name = song["player_name"], votes_to=0)
            if not any(player.name == p["name"] for p in players):
                player.wins = 0
                player = player.__dict__
                players.append(player)
            else:
                player = next((p for p in players if player.name == p["name"]), None)
            if player:
                player["votes_to"] += song["votes"]
        for name in round["winner"]:
            winner = next((p for p in players if p["name"] == name), None)
            if winner:
                winner["wins"] += 1
    players = sorted(players, key = lambda x: x["name"])
    write_json("players", players)
    return players

def export_songs(rounds):
    all_songs = []
    for round in rounds:
        song_number = 1
        if not isinstance(round, dict):
            round = round.__dict__
        for song in round["submissions"]:
            if isinstance(song, str):
                song = get_song(song)
            if not isinstance(song, dict):
                song = song.__dict__
            if not isinstance(song["voters"][0], dict):    
                song["voters"] = [vars(voter) for voter in song["voters"]]
            song["id"] = F"{song["player_name"][:3].lower()}{song_number:02d}{round["round_number"]:02d}"
            all_songs.append(song)
            song_number += 1
    songs = sorted(all_songs, key = lambda x: (x["player_name"], -x["votes"]))
    write_json("songs", songs)
    return songs

def export_rounds(rounds):
    results = []
    export_songs(rounds)
    export_players(rounds)
    for round in rounds:
        if not isinstance(round, dict):
            round = round.__dict__
        songs = []
        song_number = 1
        for song in round["submissions"]:
            if not isinstance(song, str):
                song.id = F"{song.player_name[:3].lower()}{song_number:02d}{round["round_number"]:02d}"
                songs.append(song.id)
            else:
                songs.append(song)
            song_number += 1
        if songs:
            round["submissions"] = songs
        results.append(round)
    write_json("rounds", results)   
    return results
