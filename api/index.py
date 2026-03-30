import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
# This looks for the standard keys Vercel created when you clicked "Connect"
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")

# Connect to the Redis database
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
    return datetime.utcnow() + timedelta(hours=NIGERIA_OFFSET)

def load_data():
    try:
        # Pull data from the database
        raw = redis.get("altar_v7_final")
        if raw: return json.loads(raw)
    except Exception as e:
        print(f"DB Error: {e}")
    
    # Default if database is empty
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    try:
        # Save data to the database
        redis.set("altar_v7_final", json.dumps(data))
    except Exception as e:
        print(f"Save Error: {e}")

def calculate_duration(start_str, end_str):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_str, fmt)
        t2 = datetime.strptime(end_str, fmt)
        # Handle if prayer crosses midnight
        if t2 <= t1: t2 += timedelta(days=1)
        diff = t2 - t1
        mins = int(diff.total_seconds() / 60)
        return f"{mins//60}h {mins%60}m"
    except: return "0h 0m"

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select a Name first!"
    current_data = load_data()
    now_time = get_now().strftime("%I:%M %p")
    
    for p in current_data:
        if p["n"] == name:
            if action_type == "start":
                p["st"], p["in"], p["out"], p["dur"] = "🔥 Praying", now_time, "--", ""
            elif action_type == "finish":
                if p["in"] == "--": continue
                p["st"], p["out"] = "✅ Done", now_time
                p["dur"] = calculate_duration(p["in"], now_time)
            elif action_type == "vision":
                p["v"] = vision_text
    
    save_data(current_data)
    return render_list(), f"Action recorded at {now_time}"

def render_list():
    current_pastors = load_data()
    html = "<div style='max-height: 450px; overflow-y: auto; padding: 5px;'>"
    for p in current_pastors:
        is_praying = "Praying" in p["st"]
        bg = "#D4AF37" if is_praying else "#1a1a1a"
        color = "#000" if is_praying else "#D4AF37"
        
        html += f"""<div style="background:{bg}; color:{color}; padding:15px; margin-bottom:12px; border-radius:12px; border:1px solid #D4AF37; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:1.1em;">{p['n']}</strong>
                <span style="font-weight:bold;">{p['st']}</span>
            </div>
            <div style="font-size:0.9em; margin-top:5px; opacity:0.9;">
                {p['in']} - {p['out']} {f'({p["dur"]})' if p["dur"] else ''}
            </div>"""
        if p.get('v'):
            html += f"<div style='margin-top:10px; border-top:1px dashed #555; padding-top:8px; font-style:italic;'>📜 Vision: {p['v']}</div>"
        html += "</div>"
    html += "</div>"
    return html

def reset_altar(pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), "❌ Incorrect Admin Password"
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    save_data(data)
    return render_list(), "🔄 Altar Reset Successful"

# --- GRADIO INTERFACE ---
with gr.Blocks(css=".gradio-container {background-color:#000; color:#D4AF37; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}") as demo:
    gr.HTML("<div style='text-align:center;'><h1 style='color:white; margin-bottom:0;'>PASTORIA DAILY ALTAR</h1><p style='color:#D4AF37;'>NIGERIA SPIRITUAL WATCH</p></div>")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🕯️ Live Altar")
            list_view = gr.HTML(render_list())
            
        with gr.Column(scale=1):
            gr.Markdown("### ⚔️ Priest Controls")
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Select Your Name")
            
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            
            gr.Markdown("---")
            vision_box = gr.Textbox(label="Prophetic Vision / Testimony", placeholder="Enter the word received during prayer...", lines=3)
            btn_v = gr.Button("📤 SEND VISION", variant="secondary")
            
            status = gr.Markdown("**Status:** Online")

            with gr.Accordion("🛡️ Admin Reset", open=False):
                pw = gr.Textbox(label="Enter Password", type="password")
                reset_btn = gr.Button("🔄 RESET ALL DATA", variant="stop")

    # LOGIC
    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status])
    btn_v.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status])
    reset_btn.click(reset_altar, [pw], [list_view, status])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
