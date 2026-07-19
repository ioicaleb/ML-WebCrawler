import flet as ft
from DataProcessing.data_processor import process_standings

def generate_standings_tab(page: ft.Page):
    standings_data = process_standings()
    
    standings_column = ft.Column(
        spacing=10,
        horizontal_alignment=ft.CrossAxisAlignment.START
    )

    for line in standings_data:
        standings_column.controls.append(ft.Text(line, size=32))
    
    standings_container = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[standings_column],
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