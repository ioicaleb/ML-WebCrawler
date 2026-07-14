from ExportManager import get_song

def vote_matrix_analysis(rounds):
    """
    Convert round data into a vote matrix structure for statistical analysis.
    
    This function transforms raw round data into a structured format where:
    - Each round has a list of players who submitted songs
    - Each voter has a list of votes they gave to each player
    - The matrix allows for analysis of voting patterns and preferences
    
    Args:
        rounds (list): List of round dictionaries containing submission data
        
    Returns:
        list: List of vote matrix dictionaries with structured voting data
        
    Example:
        [{
            "id": 1,
            "players": ["Alice", "Bob", "Charlie"],
            "voters": [
                {
                    "name": "Alice",
                    "votes": [
                        {"player": "Alice", "votes": 5},
                        {"player": "Bob", "votes": 3},
                        {"player": "Charlie", "votes": 2}
                    ]
                }
            ]
        }]
    """
    print("Converting results to vote matrix")
    vm_rounds = []
    
    # Process each round
    for round in rounds:
        # Initialize vote matrix structure for this round
        vm = {"id": round["round_number"], "players": [], "voters": []}
        players = []
        
        # Collect all players who submitted songs in this round
        submissions = round['submissions']
        for submission in submissions:
            song = get_song(submission)
            player_name = song["player_name"]
            if player_name not in players:
                players.append(player_name)
        
        # Sort players for consistent ordering
        players.sort()
        vm["players"] = players

        # Initialize voter tracking dictionary
        voter_dict = {}
        for submission in submissions:
            song = get_song(submission)
            player_name = song["player_name"]
            
            # Process each voter's votes for this song
            for voter in song["voters"]:
                voter_name = voter["name"]
                
                # Initialize voter data if not already present
                # Skip voters who left the league
                if voter_name not in voter_dict:
                    voter_dict[voter_name] = {player: 0 for player in players}
                
                # Add votes from this voter to the target player
                voter_dict[voter_name][player_name] += voter["votes"]
        
        # Format the final structure for voters
        vm["voters"] = []
        # Sort voters for consistent ordering
        voter_dict = dict(sorted(voter_dict.items()))
        for voter_name, votes in voter_dict.items():
            voter_votes = []
            # For each player, create a vote entry
            for target_player in players:
                voter_votes.append({
                    "player": target_player,
                    "votes": votes[target_player]
                })
            # Add voter entry to the vote matrix
            vm["voters"].append({
                "name": voter_name,
                "votes": voter_votes
            })
        
        vm_rounds.append(vm)
    return vm_rounds