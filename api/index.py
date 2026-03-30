import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION (Using the clean Names) ---
URL = os.environ.get("REDIS_URL")
TOKEN = os.environ.get("REDIS_TOKEN")
redis = Redis(url=URL, token=TOKEN) if URL and TOKEN else None

ADMIN_PASSWORD = "Admin123" 
NIGERIA_OFFSET = 1 

pastors_list = [
    {"n": "Pst Joey", "s": "10:00 PM - 11:00 PM"},
    {"n": "Pst Moses", "s": "10:00 PM - 11:00 PM"},
    {"n": "Pst Gabriel", "s": "11:00 PM - 12:00 AM"},
    {"n": "Pst Charles", "s": "12:00 AM - 01:00 AM"},
    {"n": "Pst Nosa", "s": "03:00 AM - 04:00 AM"},
    {"n": "Pst Jasper", "s": "04:00 AM - 05:00 AM"},
    {"n": "Deacon Angela", "s": "06:00 AM - 07:00 AM"},
    {"n": "Pst Seun", "s": "11:30 AM - 12:30 PM"},
    {"n": "Pst Zenith", "s": "03:00 PM - 04:00 PM"},
    {"n": "Pst Godfrey", "s": "06:00 PM - 07:00 PM"}
]

def get_now():
    return (datetime.utcnow() + timedelta(hours=NIGERIA_OFFSET)).strftime("%I:%M %p")

def calculate_hours(start_t, end_t):
    try:
        fmt = "%I:%M %p"
        t1 = datetime.strptime(start_t, fmt)
        t2 = datetime.strptime(end_t, fmt)
        if t2 <= t1: t2 += timedelta(days=1)
        diff = t2 - t1
        hrs = int(diff.total_seconds() // 3600)
        mins = int((diff.total_seconds() % 3600) // 60)
        return f"{hrs}h {mins}m"
    except: return "0h 0m"

def load_db():
    if redis:
        try:
            raw = redis.get("altar_v300_final")
            if raw: return json.loads(raw)
        except: pass
    return [{"n": p["n"], "s": p["s"], "st": "Waiting", "in": "--", "out": "--", "dur": ""} for p in pastors_list]

def render():
    db = load_db()
    total_active = sum(1 for p in db if p["in"] != "--")
    
    html = "<div style='background:#000; padding:10px;'>"
    for p in db:
        is_p = "Praying" in p["st"]
        bg = "#D4AF37" if is_p else "#FFFFFF"
        html += f"""<div style="background:{bg} !important; border:3px solid #D4AF37; padding:12px; margin-bottom:10px; border-radius:15px; color:#000 !important;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="font-size:1.2em;">{p['n']}</b> 
                <b style="font-size:1.1em;">{'🔥 ' if is_p else ''}{p['st']}</b>
            </div>
            <div style="font-size:0.95em; font-weight:bold;">
                In: {p['in']} | Out: {p['out']} 
                <span style="color:#D8000C; margin-left:10px;">{f'⏱ {p["dur"]}' if p["dur"] else ''}</span>
            </div>
        </div>"""
    return html + "</div>", f"## 📊 TOTAL PRIESTS SIGNED IN: {total_active}"

def act(name, mode):
    if not name: return render()[0], "⚠️ Select Name", render()[1]
    db = load_db()
    now = get_now()
    for p in db:
        if p["n"] == name:
            if mode == "s":
                p.update({"st": "Praying", "in": now, "out": "--", "dur": ""})
            else:
                p["st"], p["out"] = "✅ Done", now
                p["dur"] = calculate_hours(p["in"], now)
    if redis: redis.set("altar_v300_final", json.dumps(db))
    return render()[0], f"Updated: {now}", render()[1]

with gr.Blocks(css=".gradio-container {background:#000!important;}") as demo:
    # THE HEADER FROM YOUR IMAGE
    gr.HTML("""<div style='text-align:center; border:4px solid #D4AF37; padding:20px; border-radius:20px; background:#111;'>
        <h1 style='color:white !important; margin:0;'>PASTORIA DAILY PRAYER</h1>
        <p style='color:white !important; margin:5px;'>GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
        <hr style='border:0; border-top:1px solid #D4AF37; width:60%; margin:10px auto;'>
        <p style='color:#D4AF37 !important; font-weight:bold; text-transform:uppercase;'>ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
    </div>""")
    
    with gr.Row():
        with gr.Column():
            list_view = gr.HTML(render()[0])
            stats_view = gr.Markdown(render()[1])
        with gr.Column():
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Select Name")
            with gr.Row():
                s_btn = gr.Button("🔥 START", variant="primary")
                f_btn = gr.Button("✅ FINISH")
            msg = gr.Markdown("🟢 System Online")

    s_btn.click(act, [name_sel, gr.State("s")], [list_view, msg, stats_view])
    f_btn.click(act, [name_sel, gr.State("f")], [list_view, msg, stats_view])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
