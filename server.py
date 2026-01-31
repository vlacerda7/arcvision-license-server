from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/files", StaticFiles(directory="files"), name="files")
templates = Jinja2Templates(directory="templates")



def get_db():
    return sqlite3.connect("server.db")


@app.on_event("startup")
def setup():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT,
        hwid TEXT,
        activated_at TEXT
    )
    """)
    conn.commit()
    conn.close()


@app.post("/register")
def register(data: dict):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO activations (token, hwid, activated_at) VALUES (?, ?, ?)",
        (data["token"], data["hwid"], datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = get_db()
    c = conn.cursor()

    # lista ativações
    c.execute("SELECT * FROM activations ORDER BY id DESC")
    rows = c.fetchall()

    # estatísticas
    c.execute("SELECT COUNT(*) FROM activations")
    total = c.fetchone()[0]

    today = datetime.utcnow().date().isoformat()
    c.execute("SELECT COUNT(*) FROM activations WHERE activated_at LIKE ?", (today + "%",))
    today_count = c.fetchone()[0]

    c.execute("SELECT COUNT(DISTINCT hwid) FROM activations")
    unique_machines = c.fetchone()[0]

    conn.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "rows": rows,
        "total": total,
        "today": today_count,
        "machines": unique_machines
    })

@app.get("/latest")
def latest():
    return {
        "version": "1.1.0",
        "url": "http://192.168.75.78:8000/files/ArcVision_1.1.0.exe",
        "sig": "http://192.168.75.78:8000/files/ArcVision_1.1.0.exe.sig"
    }
@app.post("/revoke")
def revoke_license(data: dict):
    token = data.get("token")
    hwid = data.get("hwid")

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE licenses SET status='revoked' WHERE token=? AND hwid=?", (token, hwid))
    conn.commit()
    conn.close()

    return {"status": "revoked"}
@app.get("/license_status")
def license_status(token: str, hwid: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM licenses WHERE token=? AND hwid=?", (token, hwid))
    row = c.fetchone()
    conn.close()

    if not row:
        return {"status": "invalid"}

    return {"status": row[0]}
