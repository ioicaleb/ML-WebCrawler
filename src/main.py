import os
import hashlib
from fastapi import FastAPI, HTTPException, Body
import flet as ft
import flet.fastapi as flet_fastapi
import psycopg2
from psycopg2.extras import RealDictCursor

# ---------------------------------------------------------
# 1. DATABASE & CONFIGURATION SETUP
# ---------------------------------------------------------
# Render automatically provides DATABASE_URL when you link a Postgres instance
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Establishes a safe connection to your Render PostgreSQL instance."""
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    """Creates the database schema if it does not exist yet."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS music_leagues (
            league_id VARCHAR(100) PRIMARY KEY,
            admin_password_hash VARCHAR(128) NOT NULL,
            session_cookie TEXT NOT NULL,
            scraped_data JSONB DEFAULT '{}'::jsonb
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Initialize database schema during container boot
if DATABASE_URL:
    init_db()

# ---------------------------------------------------------
# 2. FASTAPI BACKEND (The Secure Logic Layer)
# ---------------------------------------------------------
app = FastAPI()

def hash_password(password: str) -> str:
    """Simple SHA-256 password hashing."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.get("/api/leagues/{league_id}")
def get_league_data(league_id: str):
    """Player Route: Publicly accessible cached data."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT scraped_data FROM music_leagues WHERE league_id = %s;", (league_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="League not found. Admin must set it up first.")
    return row["scraped_data"]

@app.post("/api/admin/setup")
def setup_or_update_league(payload: dict = Body(...)):
    """Admin Route: Securely creates or updates a league, then runs crawler."""
    league_id = payload.get("league_id")
    password = payload.get("password")
    cookie = payload.get("cookie")
    
    if not league_id or not password or not cookie:
        raise HTTPException(status_code=400, detail="Missing required configuration inputs.")
        
    hashed_pwd = hash_password(password)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check if league already exists
    cur.execute("SELECT admin_password_hash FROM music_leagues WHERE league_id = %s;", (league_id,))
    existing_league = cur.fetchone()
    
    if existing_league:
        # If it exists, verify the password before allowing updates
        if existing_league["admin_password_hash"] != hashed_pwd:
            cur.close()
            conn.close()
            raise HTTPException(status_code=403, detail="Invalid admin password for this league.")
            
        # Update the session cookie for the existing entry
        cur.execute(
            "UPDATE music_leagues SET session_cookie = %s WHERE league_id = %s;",
            (cookie, league_id)
        )
    else:
        # Create a brand new league record
        cur.execute(
            "INSERT INTO music_leagues (league_id, admin_password_hash, session_cookie) VALUES (%s, %s, %s);",
            (league_id, hashed_pwd, cookie)
        )
    
    conn.commit()
    cur.close()
    conn.close()

    # --- SIMULATED CRAWLER EXECUTION ---
    # Here, replace this dictionary mapping with a call to your real webcrawler script
    # e.g., mock_data = my_crawler.run(league_id, cookie)
    mock_scraped_data = {
        "league_name": f"League {league_id} Leaderboard",
        "standings": [
            {"name": "Admin User", "points": 142},
            {"name": "Player Two", "points": 115}
        ]
    }
    
    # Save the crawled contents back to the Postgres JSONB field
    import json
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE music_leagues SET scraped_data = %s WHERE league_id = %s;",
        (json.dumps(mock_scraped_data), league_id)
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"status": "Success", "message": "League updated and freshly crawled."}


# ---------------------------------------------------------
# 3. FLET FRONTEND (The Visual UI Layer)
# ---------------------------------------------------------
def flet_app(page: ft.Page):
    page.title = "Music League Hub"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    # Component State Variables
    league_id_field = ft.TextField(label="Music League ID", hint_text="e.g. 7a3b9...")
    password_field = ft.TextField(label="Admin Secret Password", password=True, can_reveal_password=True)
    cookie_field = ft.TextField(label="Session Cookie", password=True)
    status_msg = ft.Text(value="", color="blue", weight=ft.FontWeight.BOLD)
    results_column = ft.Column(spacing=5)

    def on_view_data(e):
        """Triggers local logic via API to display player stats."""
        if not league_id_field.value:
            status_msg.value = "Please enter a League ID."
            page.update()
            return
            
        # Instead of calling DB directly, Flet safely reads from the local FastAPI app
        try:
            data = get_league_data(league_id_field.value)
            status_msg.value = f"Showing: {data.get('league_name')}"
            results_column.controls.clear()
            for row in data.get("standings", []):
                results_column.controls.append(ft.Text(f"🏆 {row['name']} — {row['points']} pts"))
        except HTTPException as ex:
            status_msg.value = f"Error: {ex.detail}"
        except Exception:
            status_msg.value = "League ID not found or server offline."
        page.update()

    def on_admin_setup(e):
        """Submits setup settings over to the backend validation handler."""
        payload = {
            "league_id": league_id_field.value,
            "password": password_field.value,
            "cookie": cookie_field.value
        }
        try:
            res = setup_or_update_league(payload)
            status_msg.value = res["message"]
            cookie_field.value = ""  # Clean sensitive field text
        except HTTPException as ex:
            status_msg.value = f"Failed: {ex.detail}"
        except Exception as ex:
            status_msg.value = f"Network connection error: {str(ex)}"
        page.update()

    # Add components cleanly to the page view
    page.add(
        ft.Text("Music League Analytics Hub", size=24, weight=ft.FontWeight.BOLD),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Player Dashboard", size=16, weight=ft.FontWeight.W_600),
                    league_id_field,
                    ft.ElevatedButton("View Leaderboard Data", on_click=on_view_data, icon=ft.Icons.SEARCH),
                ]), padding=15
            )
        ),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Admin Control Setup", size=16, weight=ft.FontWeight.W_600),
                    password_field,
                    cookie_field,
                    ft.ElevatedButton("Initialize / Overwrite Config", on_click=on_admin_setup, icon=ft.Icons.SECURITY, bgcolor="amber200"),
                ]), padding=15
            )
        ),
        status_msg,
        results_column
    )

# ---------------------------------------------------------
# 4. MERGE MOUNTING & EXECUTION
# ---------------------------------------------------------
# Mounts the Flet user interface directly inside the FastAPI environment route
app.mount("/", flet_fastapi.app(flet_app))

# Render requires running via a production server command
# Setup your Render dynamic entrypoint point tool to execute: `uvicorn main:app --host 0.0.0.0 --port 8000`