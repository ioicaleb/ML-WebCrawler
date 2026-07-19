from DataCollection.export_manager import get_song
from DataCollection.json_manager import read_json, write_json

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
        round["votes"] = []
        
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
                if voter_name != "[Left the League]":
                
                # Initialize voter if not already present
                    if voter_name not in voter_dict:
                        voter_dict[voter_name] = {player: 0 for player in players}
                    
                    # Add votes from this voter to the target player
                    voter_dict[voter_name][player_name] += voter["votes"]

        dp_results = read_json("hardcoded_results")
        
        for dp_round in dp_results:
            if int(dp_round["round"]) == round["round_number"]:
                for dp in dp_round["players"]:
                    voter_name = next(iter(dp))
                    if voter_name not in voter_dict:
                        voter_dict[voter_name] = dp[voter_name]
            else:
                continue
            break

        # Format the final structure for voters
        vm["voters"] = convert_voter_dict(voter_dict, players)
        
        vm_rounds.append(vm)

        round["votes"].append(vm)

    write_json("rounds", rounds)
    return vm_rounds

def master_voter_matrix(rounds):
    matrix = [[""], ]
    players = read_json("players")
    voter_dict = {}
    
    for player in players:
        matrix[0].append(player["name"])

    for round in rounds:           
        for voter in round["voters"]:
            voter_name = voter["name"]
            
            # Initialize voter if not already present
            if voter_name not in voter_dict:
                voter_dict[voter_name] = {player["name"]: 0 for player in players}

            # Add votes from this voter to the target player
            for vote in voter["votes"]:
                voter_dict[voter_name][vote["player"]] += vote["votes"]
    players_list = []
    for player in players:
        players_list.append(player["name"])

    data = convert_voter_dict(voter_dict, players_list)

    if data:
        for player, player_data in zip(players, data):
            player["votes"] = player_data.get("votes")
        write_json("players", players)
    

    # Sort voters for consistent ordering
    matrix.extend(data)

    return matrix

def convert_voter_dict(voter_dict, players):
    data = []
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
        data.append({
            "name": voter_name,
            "votes": voter_votes
        })
    return data