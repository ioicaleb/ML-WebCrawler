from DataCollection.json_manager import read_json, write_json
from DataProcessing.data_processor import process_player_stats

def build_static_dashboard_cache():
    print("Starting local stats pre-computation...")
    
    players = read_json("players") or []
    top_songs_data = read_json("top_songs") or {}
    all_songs_data = read_json("all_songs") or {}
    round_songs_data = read_json("round_songs") or {}
    votes_from_data = read_json("votes_from") or {}
    
    cached_dashboard = {}
    
    for player in players:
        player_name = player.get("name")
        if not player_name:
            continue
            
        print(f" -> Crunching analytics for: {player_name}")
        
        player_stats_data = process_player_stats(
            player, 
            top_songs_data, 
            all_songs_data, 
            round_songs_data, 
            votes_from_data
        )
        
        cached_dashboard[player_name] = player_stats_data
        
    write_json(cached_dashboard, "precomputed_stats")
        
    print(f"Success! Generated master cache")

if __name__ == "__main__":
    build_static_dashboard_cache()