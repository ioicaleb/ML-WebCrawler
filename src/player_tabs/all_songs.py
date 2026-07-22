import flet as ft

def generate_all_songs(player_stats_data):
    all_songs_data = player_stats_data.get("all_songs") or {}

    all_songs_list =  ft.Container(
                content = ft.Column(
                    controls = [], 
                    scroll= ft.ScrollMode.HIDDEN,
                ),
                border_radius=10,
                height= 600,
                alignment=ft.Alignment.CENTER_LEFT
            )
            
    for song in all_songs_data:
        song_details = (f"{song.get('name')}\n"
                        f"Artist: {song.get('artist')}\n"
                        f"Album: {song.get('album')}\n"
                        f"Votes: {song.get('votes')}")
        all_songs_list.content.controls.append(ft.Text(song_details, size=20))
    
    all_songs = ft.Container(
        content= all_songs_list,
        expand=True,
        visible=False
    )

    return all_songs