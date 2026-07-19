from DataCollection.json_manager import read_json

songs = {}
players = {}
rounds = {}

def get_songs():
    global songs
    if not songs:
        songs = read_json("songs")
    return songs

def get_rounds():
    global rounds
    if not rounds:
        rounds = read_json("rounds")
    return rounds

def get_players():
    global players
    if not players:
        players_list = read_json("players")
        
        sorted_players = sorted(players_list, key=lambda x: x["votes_to"], reverse=True)

        for player in players_list:        
            index = next((index for index, p in enumerate(sorted_players) if p["name"] == player["name"]), None)
            player["position"] = f"#{index + 1}"
        players = players_list
    return players

def find_songs_by_title(title):
    data = []
    songs = get_songs()
    for song in songs:
        if title.lower() in song["name"].lower():
            data.append(song)
    return data

def find_song_by_id(id):
    songs = get_songs()
    for song in songs:
        if(song["id"]) == id:
            return song
    print(f"Can't find song with id {id}")

def find_songs_by_artist(artist):
    data = []
    songs = get_songs()
    for song in songs:
        if artist.lower() in song["artist"].lower():
            data.append(song)
    return data

def find_songs_by_album(album):
    data = []
    songs = get_songs()
    for song in songs:
        if album.lower() in song["album"].lower():
            data.append(song)
    return data

def find_songs_by_submitter(submitter):
    data = []
    songs = get_songs()
    for song in songs:
        if submitter.lower() == song["player_name"].lower():
            data.append(song)
    return data

def find_player_songs_by_round(player_name):
    data = []
    rounds = get_rounds()
    songs = get_songs()
    for round in rounds:
        song_data = {
            "round_id": round["round_number"],
            "title": round["title"],
            "songs": []
        }
        for song in songs:
            if song["id"] in round["submissions"] and song["player_name"] == player_name:
                song_data["songs"].append(song)    
        data.append(song_data)
    data = sorted(data, key = lambda x: x["round_id"])
    return data

def find_songs_by_voter(voter_name):
    data= []
    songs = get_songs()
    for song in songs:
        voters = song["voters"]
        for voter in voters:
            if voter["name"] == voter_name:
                data.append(song)

    data = sorted(data, key = lambda x: x["player_name"])
    return data

def find_top_songs(voter_name):
    data= []
    songs = find_songs_by_voter(voter_name)
    for song in songs:
        voters = song["voters"]
        for voter in voters:
            if voter["name"] == voter_name and voter["votes"] == 4:
                data.append(song)

    data = sorted(data, key = lambda x: x["artist"])
    return data

def get_player_avatar(player):
    global players
    
    for player_data in players:
        if player_data.get("name") == player:
            return player_data.get("avatar")