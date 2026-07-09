class Player:
    def __init__(self):
        self.name = None
        self.songs = []
        self.votes_to = 0
        self.voters = []

class Round:
    def __init__(self, title, round_number, description, submissions):
        self.title = title
        self.round_number = round_number
        self.description = description
        self.submissions = submissions
            
class Voter:
    def __init__(self, player_name, points, comment = ""):
        self.player_name = player_name
        self.points = points
        self.comment = comment

class Song:
    def __init__(self, name, votes = 0, player_name = None, artist = None, album = None):
        self.name = name
        self.artist = artist
        self.album = album
        self.player_name = player_name
        self.votes = votes
        self.voters = []