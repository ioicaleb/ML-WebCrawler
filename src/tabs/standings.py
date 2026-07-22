import flet as ft
from data_processing.data_processor import process_standings_votes, process_standings_wins, process_standings_comments

def generate_standings_tab(page: ft.Page):
    votes_data = process_standings_votes()
    wins_data = process_standings_wins()
    comments_data = process_standings_comments()
    
    votes_column = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )

    for line in votes_data:
        votes_column.controls.append(ft.Text(line, size=32))


    wins_column = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )

    for line in wins_data:
        wins_column.controls.append(ft.Text(line, size=32))

    comments_column = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )
    
    for line in comments_data:
        comments_column.controls.append(ft.Text(line, size=32))


    tab_view = ft.Tabs(
            length=5,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Votes", icon=ft.Icons.HOW_TO_VOTE),
                            ft.Tab(label="Wins", icon=ft.Icons.DIAMOND),
                            ft.Tab(label="Comments", icon=ft.Icons.CHAT_BUBBLE)
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            votes_column,
                            wins_column,
                            comments_column
                        ]
                    )
                ]
            )
        )
    
    standings_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[tab_view],
                        width=600,
                        margin = ft.Margin(200, 0, 0, 0),
                        expand=False,     
                        scroll=ft.ScrollMode.HIDDEN
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            expand=True
        )

    return standings_container