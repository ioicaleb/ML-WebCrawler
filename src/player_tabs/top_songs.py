import flet as ft

def generate_top_songs(player_stats_data):
    top_songs_data = player_stats_data.get("top_songs") or {}
    top_songs_list = ft.Container(
        content = ft.Column(
            controls = [], 
            scroll= ft.ScrollMode.HIDDEN,
        ),
        border_radius=10,
        alignment=ft.Alignment.CENTER_LEFT
    )

    for song in top_songs_data:
        song_details = (f"{song.get('name')}\n"
                        f"Artist: {song.get('artist')}\n"
                        f"Album: {song.get('album')}\n"
                        f"Submitted By: {song.get('player_name')}")
        top_songs_list.content.controls.append(ft.Text(song_details, size=20))

    top_songs = ft.Container(
        content= top_songs_list,
        expand=True,
        visible=False
    )

    return top_songs