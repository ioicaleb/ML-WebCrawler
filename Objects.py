class Player_Defunct:
    def __init__(self):
        self.name = ""
        self.songs = []

class Player:
    def __init__(self, name = "", votes_to = 0):
        self.name = name
        self.votes_to = votes_to
        self.wins = 0

class Round:
    def __init__(self, title, round_number, description, submissions):
        self.title = title
        self.round_number = round_number
        self.description = description
        self.submissions = submissions
        self.winner = self.determine_winner(submissions)
    
    def determine_winner(self, submissions):
        winners = []
        for submission in submissions:
            if submission.votes == submissions[0].votes:
                winners.append(submission.player_name)
            else:
                break
        return winners
            
class Voter:
    def __init__(self, name, votes, comment = ""):
        self.name = name
        self.votes = votes
        self.comment = comment

class Song:
    def __init__(self, name, votes = 0, player_name = None, artist = None, album = None, voters = []):
        self.name = name
        self.artist = artist
        self.album = album
        self.player_name = player_name
        self.votes = votes
        self.voters = voters
    
def convert_username_to_name(username, active_players, defunct_players = [], name = ""):
    for player in active_players:
        if username == player[0]:
            return player[1]
    if defunct_players and name:
        for player in defunct_players:
            if next((s for s in player["songs"] if name == s), None):
                return player["name"]
    return "[Left the League]"
        