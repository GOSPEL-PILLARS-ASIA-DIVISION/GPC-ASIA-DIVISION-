import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

redis = None
if REDIS_URL and REDIS_TOKEN:
    try:
        redis = Redis(url=REDIS_URL, token=REDIS_TOKEN)
    except:
        redis = None

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
    return datetime.utcnow() + timedelta(hours=NIGERIA_OFFSET)

def load_data():
    if redis:
        try:
            raw = redis.get("altar_asia_v25")
            if raw: return json.loads(raw)
        except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "v": ""})
    return data

def save_data(data):
    if redis:
        try: redis.set("altar_asia_v25", json.dumps(data))
        except: pass

def render_list():
    current_pastors = load_data()
    html = "<h3 style='color: white; margin-left: 10px;'>Altar Watch List</h3>"
    html += "<div style='max-height: 450px; overflow-y: auto; padding: 10px; background-color: #000;'>"
    for p in current_pastors:
        is_praying = "Praying" in p["st"]
        bg = "#D4AF37" if is_praying else "#FFFFFF"
        txt = "#000000"
        
        html += f"""<div style="background:{bg}; border: 3px solid #D4AF37; padding:15px; margin-bottom:12px; border-radius:15px; color:{txt}; font-family: sans-serif;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <b style="font-size:1.3em;">{p['n']}</b><br>
                    <span style="font-size:0.9em; opacity: 0.8;">{p['s']}</span>
                </div>
                <div style="text-align:right;">
                    <b style="font-size:1.1em;">{p['st']}</b><br>
                    <span style="font-size:0.9em;">{p['in']} - {p['out']}</span>
                </div>
            </div>
        </div>"""
    html += "</div>"
    return html

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select Name"
    current_data = load_data()
    now_time = get_now().strftime("%I:%M %p")
    for p in current_data:
        if p["n"] == name:
            if action_type == "start": p.update({"st": "🔥 Praying", "in": now_time, "out": "--"})
            elif action_type == "finish": p.update({"st": "✅ Done", "out": now_time})
            elif action_type == "vision": p["v"] = vision_text
    save_data(current_data)
    return render_list(), f"Recorded at {now_time}"

def admin_reset(pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), "❌ Denied"
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "v": ""})
    save_data(data)
    return render_list(), "🔄 Altar Reset"

# --- THE UI DESIGN ---
with gr.Blocks(css=".gradio-container {background-color: #000 !important;} * {color: #D4AF37 !important;}") as demo:
    
    # MATCHING THE HEADER FROM YOUR IMAGE
    gr.HTML("""
        <div style='text-align:center; padding:30px; border: 4px solid #D4AF37; border-radius: 20px; margin-bottom: 20px;'>
            <h1 style='color:white !important; margin:0; font-size: 2.5em; letter-spacing: 2px;'>PASTORIA DAILY PRAYER</h1>
            <p style='color:white !important; margin: 10px 0; font-size: 1.1em;'>GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
            <p style='color:#D4AF37 !important; font-weight: bold; font-size: 1.1em; text-transform: uppercase;'>
                ASIA DIVISION HEAD | APOSTEL SOLOMON SUCCESS
            </p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            list_view = gr.HTML(render_list())
            
        with gr.Column(scale=1):
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Choose Name")
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            
            vision_box = gr.Textbox(label="Vision / Word", lines=3)
            btn_v = gr.Button("📤 SEND VISION")
            
            status_msg = gr.Markdown("🟢 Ready")

            with gr.Accordion("🛡️ Admin Panel", open=False):
                pw = gr.Textbox(label="Password", type="password")
                reset_btn = gr.Button("RESET FOR NEW DAY", variant="stop")

    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status_msg])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status_msg])
    btn_v.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status_msg])
    reset_btn.click(admin_reset, [pw], [list_view, status_msg])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
