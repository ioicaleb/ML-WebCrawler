from Objects import Player
from Objects import Song


def parse_players(values):
    players = []

    if not values:
        print("No data found.")
        return

    i = 0
    while i < len(values[0]):
        player = Player()
        j = 0
        for row in values:
            j += 1
            if i >= len(row) or not row[i]:
                break
            if j == 1:
                player.name = row[i]
                continue
            if (i + 1) >= len(row) or not row[i + 1]:
                break
            if j == 2:
                continue
            
            song = Song(row[i], int(row[i + 1]))
            player.songs.append(song)

        if player.name is not None:
            player.songs.sort(key=lambda x: (x.votes_total), reverse=True)
            players.append(player)

        i += 2
    return players