import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION WITH SAFETY SHIELD ---
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

# This prevent the 500 Error if variables are missing
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
            raw = redis.get("altar_v16_final")
            if raw: return json.loads(raw)
        except: pass
    
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    if redis:
        try: redis.set("altar_v16_final", json.dumps(data))
        except: pass

def calculate_duration(start_str, end_str):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_str, fmt)
        t2 = datetime.strptime(end_str, fmt)
        if t2 <= t1: t2 += timedelta(days=1)
        diff = t2 - t1
        mins = int(diff.total_seconds() / 60)
        return f"{mins//60}h {mins%60}m"
    except: return "0h 0m"

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select Name", get_stats()
    current_data = load_data()
    now_time = get_now().strftime("%I:%M %p")
    for p in current_data:
        if p["n"] == name:
            if action_type == "start": p.update({"st": "🔥 PRAYING", "in": now_time, "out": "--", "dur": ""})
            elif action_type == "finish":
                if p["in"] == "--": continue
                p.update({"st": "✅ DONE", "out": now_time, "dur": calculate_duration(p["in"], now_time)})
            elif action_type == "vision": p["v"] = vision_text
    save_data(current_data)
    return render_list(), f"Recorded: {now_time}", get_stats()

def get_stats():
    data = load_data()
    total_in = sum(1 for p in data if p["in"] != "--")
    return f"### 📊 PRIESTS ACTIVE: {total_in}"

def render_list():
    current_pastors = load_data()
    html = "<div style='max-height: 450px; overflow-y: auto; padding: 10px; background-color: #000;'>"
    for p in current_pastors:
        is_praying = "PRAYING" in p["st"]
        bg = "#D4AF37" if is_praying else "#222"
        txt = "#000 !important" if is_praying else "#FFF !important"
        html += f"""<div style="background:{bg} !important; border: 1px solid #D4AF37; padding:12px; margin-bottom:8px; border-radius:8px; color:{txt}; font-family: Arial;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="color:{txt};">{p['n']}</b>
                <b style="color:{txt};">{p['st']}</b>
            </div>
        </div>"""
    html += "</div>"
    return html

# --- THE UI ---
with gr.Blocks(css=".gradio-container {background-color: #000 !important;} * {color: #D4AF37 !important;}") as demo:
    gr.HTML("<div style='text-align:center; border:2px solid #D4AF37; padding:10px; border-radius:10px;'><h1 style='color:white !important;'>NIGERIA SPIRITUAL WATCH</h1><p>PASTORIA DAILY ALTAR</p></div>")
    
    with gr.Row():
        with gr.Column():
            list_view = gr.HTML(render_list())
            stats_view = gr.Markdown(get_stats())
        with gr.Column():
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Priest Name")
            with gr.Row():
                btn_in = gr.Button("🔥 START")
                btn_out = gr.Button("✅ FINISH")
            vision_box = gr.Textbox(label="Vision", lines=2)
            btn_v = gr.Button("📤 SEND")
            
            with gr.Accordion("🛡️ Admin", open=False):
                pw = gr.Textbox(label="Password", type="password")
                reset_btn = gr.Button("RESET ALTAR")

    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, gr.Markdown(), stats_view])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, gr.Markdown(), stats_view])
    btn_v.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, gr.Markdown(), stats_view])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
