"""
export_manager.py - Data export module for ML WebCrawler

This module handles parsing and compiling in-memory structures for database tracking:
- Exporting player information
- Exporting song information
- Exporting round information
"""

from data_collection.objects import Player

# Use pure in-memory lists for data scoping across runtime threads
_cached_songs_array = []

def get_song(song_id: str) -> dict:
    """
    Retrieve a song by its ID from the active in-memory cache list.
    """
    global _cached_songs_array
    
    try:
        # Find and return the song with a matching ID directly from memory
        song = [s for s in _cached_songs_array if s.get('id') == song_id][0]
        if song:
            return song
    except IndexError:
        print(f"Could not find song with id {song_id}")
        raise

def export_players(rounds: list, current_avatars_cache: dict) -> list:
    """
    Export and compute player statistics dynamically from your memory records.
    
    Args:
        rounds (list): List of round dictionary structures.
        current_avatars_cache (dict): In-memory avatar dictionary mapping player_name -> avatar_url
        
    Returns:
        list: Sorted list of player analytics dictionaries.
    """
    players = []
    
    # Process each round
    for round_obj in rounds:
        # Fallback check if objects somehow managed to sneak past pre-serialization
        if hasattr(round_obj, "__dict__"):
            round_obj = round_obj.__dict__
        
        # Process each submission in the round
        for song in round_obj.get("submissions", []):
            if isinstance(song, str):
                song = get_song(song)
            elif hasattr(song, "__dict__"):
                song = song.__dict__
            
            player_name = song.get("player_name", "Unknown")
            song_votes = song.get("votes", 0)
            
            # Check if player already exists in our compiled tracking list
            existing_player = next((p for p in players if p["name"] == player_name), None)
            
            if not existing_player:
                # Map avatar URL directly using our live memory dictionary lookups
                avatar_url = current_avatars_cache.get(player_name, "")
                
                players.append({
                    "name": player_name,
                    "votes_to": song_votes,
                    "wins": 0,
                    "avatar": avatar_url
                })
            else:
                # Update existing player's raw vote accumulation tracking metric
                existing_player["votes_to"] += song_votes
        
        # Process winners for each round
        for name in round_obj.get("winner", []):
            winner = next((p for p in players if p["name"] == name), None)
            if winner:
                winner["wins"] += 1
    
    # Sort players uniformly by their display name properties
    players = sorted(players, key=lambda x: x["name"])
    return players

def export_songs(rounds: list) -> list:
    """
    Export song datasets from rounds, assigning unique IDs for indexing.
    """
    global _cached_songs_array
    all_songs = []
    
    # Process each round
    for round_obj in rounds:
        song_number = 1
        if hasattr(round_obj, "__dict__"):
            round_obj = round_obj.__dict__
        
        # Process each submission in the round
        for song in round_obj.get("submissions", []):
            if isinstance(song, str):
                song = get_song(song)
            elif hasattr(song, "__dict__"):
                song = song.__dict__
            
            # Convert internal Voter objects to dicts if they aren't already formatted
            voters_list = song.get("voters", [])
            if voters_list and not isinstance(voters_list[0], dict):    
                song["voters"] = [vars(voter) if hasattr(voter, "__dict__") else voter for voter in voters_list]
            
            # Generate a clean, unique indexing ID string for tracking
            song["id"] = f"{song['player_name'][:3].lower()}{song_number:02d}{round_obj['round_number']:02d}"
            all_songs.append(song)
            song_number += 1
            
    # Update our global memory reference so get_song() can cross-index elements seamlessly
    _cached_songs_array = sorted(all_songs, key=lambda x: (x["player_name"], -x["votes"]))
    return _cached_songs_array

def export_rounds(rounds: list, current_avatars_cache: dict) -> list:
    """
    Compiles standard rounds data frames, extracting and processing child caches.
    """
    # Build your song and player cache matrices inside memory variables
    export_songs(rounds)
    export_players(rounds, current_avatars_cache)
    
    results = []
    
    # Process each round
    for round_obj in rounds:
        if hasattr(round_obj, "__dict__"):
            round_obj = round_obj.__dict__
        
        songs_list = []
        song_number = 1
        
        # Isolate submissions mapping down to a list of IDs to shrink payload sizes
        for song in round_obj.get("submissions", []):
            if not isinstance(song, str):
                s_name = song.get("player_name", "unk") if isinstance(song, dict) else song.player_name
                song_id = f"{s_name[:3].lower()}{song_number:02d}{round_obj['round_number']:02d}"
                songs_list.append(song_id)
            else:
                songs_list.append(song)
            song_number += 1
        
        if songs_list:
            round_obj["submissions"] = songs_list
        
        results.append(round_obj)
        
    return results