"""
data_collector.py - Main execution module for ML WebCrawler

This module serves as the entry point for the web crawler application,
handling the main workflow of fetching data, processing results,
and exporting to spreadsheet.

Functions:
    collect_data() - Main execution function that orchestrates the crawling process
"""

from data_collection.web_crawler import get_results, check_for_new_rounds
from data_collection.export_manager import export_players, export_songs
from data_processing.json_manager import read_json

songs = {}
players = {}
results = {}
config = None

def collect_data():
    """
    Main execution function that orchestrates the crawling process.
    
    This function:
    1. Reads configuration
    2. Sets up spreadsheet ID
    3. Checks for existing results
    4. Handles new rounds detection
    5. Processes results and exports to spreadsheet
    6. Performs statistical analysis
    """
    # Read configuration from JSON
    global songs
    global players
    global config
    global results

    config = read_json("config")
    
    
    # Attempt to read existing results from JSON
    results = read_json("rounds")
    
    if results:
        print("Pulled previous results")
        
        # Try to read cached songs and players
        songs = read_json("songs")
        players = read_json("players")

    else:
        # No existing results, fetch new ones
        results = get_results(config)

def new_round_check(): 
    global songs
    global players
    global config
    global results

    # Check if we have both songs and players cached
    if songs and players:
        # Get the last round number from existing results
        last_round_number = results[-1]["round_number"]
        
        # Check if there are new rounds available
        if check_for_new_rounds(last_round_number, config):
            # Re-read songs and players (in case they were updated)
            songs = read_json("songs")
            players = read_json("players")
        
    # Handle case where cache is missing
    elif not songs:
        # Export songs and players to create cache
        export_songs(results)
        export_players(results)
        print("Failed to get songs cache")
    else:
        # Export players only
        export_players(results)
        print("Failed to get players cache") 
    
    # Process results if they were successfully obtained
    if results:
        print("Results successfully obtained")
