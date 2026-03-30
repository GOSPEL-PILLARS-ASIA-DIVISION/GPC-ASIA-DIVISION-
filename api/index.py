import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
# We use the REST client for maximum stability on Vercel
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)

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

def load_data():
    try:
        raw = redis.get("altar_asia_stable_v50")
        if raw: return json.loads(raw)
    except: pass
    return [{"n": p["n"], "s": p["s"], "st": "Waiting", "in": "--", "out": "--", "v": ""} for p in pastors_list]

def save_data(data):
    try: redis.set("altar_asia_stable_v50", json.dumps(data))
    except: pass

def render_list():
    data = load_data()
    html = "<div style='background-color:#000; padding:10px;'>"
    for p in data:
        is_praying = "Praying" in p["st"]
        # FIRE SIGN logic: if praying, use Gold background. If waiting, use White.
        bg = "#D4AF37" if is_praying else "#FFFFFF"
        status_text = f"🔥 {p['st']}" if is_praying else p["st"]
        
        html += f"""<div style="background:{bg} !important; border: 3px solid #D4AF37; padding:15px; margin-bottom:12px; border-radius:15px; color:#000 !important; font-family: sans-serif;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b style="font-size:1.2em; color:#000 !important;">{p['n']}</b><br>
                    <span style="font-size:0.9em; color:#000 !important;">{p['s']}</span>
                </div>
                <div style="text-align:right;">
                    <b style="font-size:1.1em; color:#000 !important;">{status_text}</b><br>
                    <span style="font-size:0.9em; color:#000 !important;">{p['in']} - {p['out']}</span>
                </div>
            </div>
        </div>"""
    return html + "</div>"

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select a Name First"
    db = load_data()
    now_time = get_now()
    for p in db:
        if p["n"] == name:
            if action_type == "start":
                p.update({"st": "Praying", "in": now_time, "out": "--"})
            elif action_type == "finish":
                p.update({"st": "✅ Done", "out": now_time})
            elif action_type == "vision":
                p["v"] = vision_text
    save_data(db)
    return render_list(), f"Last Action: {now_time}"

def admin_reset(pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), "❌ Denied"
    new_db = [{"n": p["n"], "s": p["s"], "st": "Waiting", "in": "--", "out": "--", "v": ""} for p in pastors_list]
    save_data(new_db)
    return render_list(), "🔄 Altar Reset Successful"

# --- THE UI DESIGN (MATCHING YOUR IMAGE) ---
with gr.Blocks(css=".gradio-container {background-color: #000 !important;} * {color: #D4AF37 !important;}") as demo:
    
    # FORCED TITLE BLOCK
    gr.HTML("""
        <div style='text-align:center; padding:25px; border: 4px solid #D4AF37; border-radius: 20px; margin-bottom: 20px; background-color: #111;'>
            <h1 style='color:white !important; margin:0; font-size: 2.2em; font-family: serif;'>PASTORIA DAILY PRAYER</h1>
            <p style='color:white !important; margin: 5px 0; font-size: 1.1em;'>GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
            <hr style='border: 0; border-top: 1px solid #D4AF37; width: 60%; margin: 10px auto;'>
            <p style='color:#D4AF37 !important; font-weight: bold; font-size: 1.1em; text-transform: uppercase;'>
                ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS
            </p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            list_view = gr.HTML(render_list())
            
        with gr.Column(scale=1):
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="1. Select Your Name")
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            
            vision_box = gr.Textbox(label="2. Prophetic Word/Vision", lines=3)
            btn_v = gr.Button("📤 SEND VISION")
            
            status_msg = gr.Markdown("🟢 System Online")

            with gr.Accordion("🛡️ Admin Panel", open=False):
                pw = gr.Textbox(label="Admin Password", type="password")
                reset_btn = gr.Button("RESET ALL DATA", variant="stop")

    # LOGIC
    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status_msg])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status_msg])
    btn_v.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status_msg])
    reset_btn.click(admin_reset, [pw], [list_view, status_msg])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
