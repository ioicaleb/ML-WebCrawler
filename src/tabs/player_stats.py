import flet as ft
from data_processing.data_processor import get_players
from data_processing.cache_manager import read_json

# Import your explicit nested stat player layout sub-tabs
from player_tabs.top_songs import generate_top_songs
from player_tabs.all_songs import generate_all_songs
from player_tabs.round_songs import generate_round_songs
from player_tabs.votes_from import generate_votes_from
from player_tabs.votes_to import generate_votes_to
from player_tabs.player_stats import generate_player_stats
from player_tabs.votes_songs import generate_votes_songs

def generate_profile_tab(page: ft.Page, return_callback):
    """
    Renders an interactive player profile selection portal, allowing 
    deep-dive exploration of sub-tab stats caches inside memory variables.
    """
    profiles_list = ft.ListView(expand=True, spacing=10, padding=10)
    players_data = get_players() or []

    def return_to_players(e):
        page.controls.clear()
        return_callback(page)

    async def get_player_profile(player: dict):
        page.splash = ft.ProgressBar()
        page.update()

        name = player.get("name", "Unknown")

        # FIXED: Removed the redundant .get(name) layer since cache_manager un-nests individual profiles directly!
        player_stats_data = read_json(f"precomputed_stats_{name}") or {}

        page.splash = None
        page.controls.clear()

        back_button = ft.Button(
            content="Back",
            icon=ft.Icons.ARROW_BACK,
            on_click=return_to_players
        )
        
        # Pull live external image URL directly from your DB cache payload maps
        local_img_path = player_stats_data.get("avatar_url")
        if local_img_path:
            avatar = ft.Image(src=local_img_path, width=100, height=100, fit=ft.ImageFit.COVER, border_radius=50)
        else:
            avatar = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=100, color=ft.Colors.GREY_600)

        # Hydrate internal metrics calculation tab containers
        top_songs = generate_top_songs(player_stats_data)
        all_songs = generate_all_songs(player_stats_data)
        round_songs = generate_round_songs(player_stats_data)
        votes_from = generate_votes_from(player_stats_data, name)
        votes_to = generate_votes_to(player_stats_data)
        player_stats = generate_player_stats(player_stats_data)
        votes_songs = generate_votes_songs(player_stats_data, name)

        views_map = {
            f"{name}'s Stats": player_stats,
            f"{name}'s Songs": all_songs,
            "Favorite Songs": top_songs,
            "Songs By Round": round_songs,
            f"Who Voted For {name}": votes_to,
            f"How {name} Voted": votes_from,
            f"Songs {name} Voted For": votes_songs
        }

        # FIXED: Ensure only the FIRST sub-tab is displayed initially; hide the rest to prevent stacked alignment overflow
        first_title = list(views_map.keys())[0]
        for t_key, container in views_map.items():
            container.visible = (t_key == first_title)

        def handle_menu_click(e):
            clicked_title = e.control.content.value
            is_dark_mode = page.theme_mode == ft.ThemeMode.DARK
            default_color = ft.Colors.WHITE if is_dark_mode else ft.Colors.BLACK

            for title, view_container in views_map.items():
                if title == clicked_title:
                    view_container.visible = True
                else:
                    view_container.visible = False
            
            try:
                main_row_split = profile_view.controls[3]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    if button.content.value == clicked_title:
                        button.content.color = ft.Colors.PURPLE_500
                    else:
                        button.content.color = default_color
            except Exception:
                e.control.content.color = ft.Colors.PURPLE_500
            
            page.update()

        def toggle_theme(e):
            if page.theme_mode == ft.ThemeMode.DARK:
                page.theme_mode = ft.ThemeMode.LIGHT
                theme_switch.icon = ft.Icons.BRIGHTNESS_7
            else:
                page.theme_mode = ft.ThemeMode.DARK
                theme_switch.icon = ft.Icons.BRIGHTNESS_4

            is_dark_mode = page.theme_mode == ft.ThemeMode.DARK
            default_color = ft.Colors.WHITE if is_dark_mode else ft.Colors.BLACK
            
            try:
                main_row_split = profile_view.controls[3]
                left_menu_container = main_row_split.controls[0]
                actual_menu_column = left_menu_container.content

                for button in actual_menu_column.controls:
                    if button.content.color != ft.Colors.PURPLE_500:
                        button.content.color = default_color
            except Exception:
                e.control.content.color = ft.Colors.PURPLE_500
            page.update()
    
        theme_switch = ft.IconButton(
            icon=ft.Icons.BRIGHTNESS_4,
            on_click=toggle_theme,
            tooltip="Toggle Dark Mode"
        )

        profile_view = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            ft.Container(content=back_button, margin=ft.Margin(0, 10, 0, 20)), 
                            ft.Row(controls=[ft.Text("Eric the Data Manager", size=42, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(content=theme_switch, right=10, top=0)
                        ],
                        height=60,
                    ),
                ),
                ft.Row(
                    controls=[
                        avatar,
                        ft.Column([
                            ft.Text(player.get('name', 'Player'), size=32, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{player.get('position', '#?')} — Accumulation: {player.get('votes_to', 0)} Votes Received", size=20)
                        ])
                    ],
                    spacing=20
                ),
                ft.Divider(height=40, color=ft.Colors.GREY_800),
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    alignment=ft.MainAxisAlignment.START,
                    expand=True,
                    controls=[
                        ft.Container(
                            margin=ft.Margin(20, 0, 0, 0),
                            content=ft.Column(
                                alignment=ft.MainAxisAlignment.START,
                                spacing=15,
                                controls=[
                                    ft.TextButton(
                                        content=ft.Text(
                                            title, 
                                            size=18, 
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.PURPLE_500 if title == first_title else (ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK)
                                        ),
                                        on_click=handle_menu_click,
                                        style=ft.ButtonStyle(padding=0)
                                    ) for title in views_map.keys()
                                ],
                            ),
                        ),
                        ft.VerticalDivider(width=40, color=ft.Colors.GREY_800),
                        ft.Container(
                            margin=ft.Margin(20, 0, 0, 0),
                            expand=True,
                            content=ft.Column(
                                expand=True,
                                controls=list(views_map.values()), # Maps sub-tab layers safely into layout engines
                            ),
                        )
                    ],
                ),
            ],
        )
        
        page.add(profile_view)
        page.update()

    # Factory lambda generation tool to handle loop variable closures correctly
    def create_click_handler(target_player):
        return lambda e: page.run_task(get_player_profile, target_player)
    
    if isinstance(players_data, dict):
        for name, player_object in players_data.items():
            if isinstance(player_object, dict):
                if "name" not in player_object:
                    player_object["name"] = name
                
                # FIXED: Removed the redundant nested .get(name) lookups
                player_stats_data = read_json(f"precomputed_stats_{name}") or {}
                local_img_path = player_stats_data.get("avatar_url")

                if local_img_path:            
                    avatar_icon = ft.Container(
                        content=ft.Image(src=local_img_path, fit="cover", border_radius=25, width=80),
                        width=80, height=80, border_radius=40, border=ft.BorderSide(2, ft.Colors.RED_300)
                    )
                else:
                    avatar_icon = ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color=ft.Colors.RED_500)
                
                profiles_list.controls.append(
                    ft.ListTile(
                        leading=avatar_icon,
                        title=ft.Text(str(name), size=22, weight=ft.FontWeight.BOLD),
                        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                        on_click=create_click_handler(player_object)
                    )
                )
            elif isinstance(players_data, list):
                for player_object in players_data:
                    if isinstance(player_object, dict):
                        name = player_object.get("name") or player_object.get("player") or "Unknown"
                        
                        # FIXED: Removed the redundant nested .get(name) lookups
                        player_stats_data = read_json(f"precomputed_stats_{name}") or {}
                        local_img_path = player_stats_data.get("avatar_url")

                        if local_img_path:            
                            avatar_icon = ft.Container(
                                content=ft.Image(src=local_img_path, fit="cover", border_radius=25, width=80),
                                width=80, 
                                height=80, 
                                border_radius=40, 
                                border=ft.BorderSide(2, ft.Colors.RED_500)
                            )
                        else:
                            avatar_icon = ft.Container(
                                content=ft.Icon(ft.Icons.PERSON, color=ft.Colors.RED_300, width=80),
                                width=80, 
                                height=80, 
                                border_radius=40, 
                                border=ft.BorderSide(2, ft.Colors.RED_500)
                            )

                        profiles_list.controls.append(
                            ft.ListTile(
                                leading=avatar_icon,
                                title=ft.Text(name, size=22, weight=ft.FontWeight.BOLD),
                                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT),
                                on_click=create_click_handler(player_object)
                            )
                        )

            profiles_container = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Column(
                            controls=[profiles_list],
                            width=500,
                            expand=False,
                            scroll=ft.ScrollMode.ALWAYS # FIXED: ScrollMode.ALWAYS ensures lengthy rosters scroll nicely
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    expand=True
                ),
                expand=True
            )

    return profiles_container