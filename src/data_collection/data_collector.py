"""
data_collector.py - Main execution module for ML WebCrawler

This module serves as the entry point for the web crawler application,
handling the main workflow of fetching data, processing results,
and exporting database analytics states.
"""

from data_collection.web_crawler import get_results, check_for_new_rounds, load_avatar_cache, get_avatar_cache
from data_collection.export_manager import export_players, export_songs

# FIXED: Removed the 'src.' prefix from internal directory references to protect Uvicorn imports
from data_processing.cache_builder import build_static_dashboard_cache
from data_processing.cache_manager import initialize_memory_cache

# Maintain structural memory states during a single orchestration invocation
songs = {}
players = {}
results = {}

def run_pipeline_migration(league_id: str, cookie: str, browser_type: str, cached_db_data: dict) -> dict:
    global songs, players, results
    
    # 1. Structure configuration variables dynamically from Flet Setup UI inputs
    config = {
        "league_id": league_id,
        "session_cookie": cookie,
        "browser_type": browser_type,
        "username-player_name": cached_db_data.get("username_mapping", {})
    }
    
    # 2. Synchronize your in-memory avatar cache with historical PostgreSQL records
    load_avatar_cache(cached_db_data.get("avatars", {}))
    
    # 3. Extract previously cached elements from your database instead of local JSON files
    results = cached_db_data.get("rounds", [])
    songs = cached_db_data.get("songs", {})
    players = cached_db_data.get("players", {})

    # 4. FIXED: Orchestrate the execution loop context to fill your global dictionary states
    if results:
        print(f"Pulled previous results from database for league: {league_id}")
        
        # Seed cache manager with existing database profile states before verifying changes
        initialize_memory_cache({
            "rounds": results,
            "songs": songs,
            "players": players
        })
        new_round_check(config)
    else:
        print("No existing results found inside PostgreSQL. Initializing full Selenium scrape sequence...")
        results = get_results(config)
        
        # Pre-seed cache manager with initial raw round text arrays so export utilities track them safely
        initialize_memory_cache({"rounds": results})
        new_round_check(config)

    # 5. FIXED: Re-hydrated the master cache manager proxy with all fully populated variables
    # This guarantees that data processing scripts like find_top_songs() read data successfully
    current_working_data = {
        "players": players,
        "rounds": results,
        "songs": songs
    }
    initialize_memory_cache(current_working_data)

    # 6. Run your precomputed master analytical statistics caches in-memory
    cache_results = build_static_dashboard_cache(current_working_data)
    processed_players = cache_results.get("players", [])
    precomputed_dashboard_stats = cache_results.get("precomputed_stats", {})
    
    # Pull down the updated avatar states after parsing loops conclude
    updated_avatars = get_avatar_cache()

    # 7. Pack and return a single unified JSON structure to be written directly to PostgreSQL JSONB
    return {
        "rounds": results,
        "songs": songs,
        "players": processed_players,
        "precomputed_stats": precomputed_dashboard_stats,
        "avatars": updated_avatars,
        "username_mapping": config["username-player_name"]
    }

def new_round_check(config): 
    global songs, players, results
    
    # Pull down the current active avatar tracking state from memory
    from data_collection.web_crawler import get_avatar_cache
    current_avatars = get_avatar_cache()

    if songs and players:
        last_round_number = results[-1]["round_number"] if isinstance(results, list) and results else 0
        updated_results = check_for_new_rounds(last_round_number, config, existing_rounds_cache=results)
        
        if updated_results != results:
            results = updated_results
            songs = export_songs(results)
            players = export_players(results, current_avatars) # Injected live memory avatars
        
    elif not songs:
        songs = export_songs(results)
        players = export_players(results, current_avatars) # Injected live memory avatars
        print("Initialized missing song/player state matrix data records")
    else:
        players = export_players(results, current_avatars) # Injected live memory avatars
