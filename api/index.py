import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
redis = Redis(
    url=os.environ.get("UPSTASH_REDIS_REST_URL"), 
    token=os.environ.get("UPSTASH_REDIS_REST_TOKEN")
)

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

def get_nigeria_time():
    return datetime.utcnow() + timedelta(hours=NIGERIA_OFFSET)

def load_data():
    try:
        raw = redis.get("nigeria_altar_v5") # New version key for clean test
        if raw: return json.loads(raw)
    except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    redis.set("nigeria_altar_v5", json.dumps(data))

def calculate_duration(start_str, end_str):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_str, fmt)
        t2 = datetime.strptime(end_str, fmt)
        if t2 < t1: t2 += timedelta(days=1)
        diff = t2 - t1
        mins = int(diff.total_seconds() / 60)
        return f"{mins//60}h {mins%60}m"
    except: return ""

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select a name!"
    current_data = load_data()
    now_time = get_nigeria_time().strftime("%I:%M %p")
    msg = ""
    
    for p in current_data:
        if p["n"] == name:
            if action_type == "start":
                p["st"], p["in"], p["out"], p["dur"] = "🔥 Praying", now_time, "--", ""
                msg = f"🙏 Prayer started at {now_time}"
            elif action_type == "finish":
                p["st"], p["out"] = "✅ Done", now_time
                p["dur"] = calculate_duration(p["in"], now_time)
                msg = f"🙌 Prayer finished at {now_time}"
            elif action_type == "vision":
                p["v"] = vision_text # SAVING THE VISION
                msg = "📤 Vision Sent to the Altar!"
    
    save_data(current_data)
    return render_list(), msg

def render_list():
    current_pastors = load_data()
    html = "<div style='max-height: 500px; overflow-y: auto; padding: 5px;'>"
    for p in current_pastors:
        is_praying = "Praying" in p["st"]
        bg = "linear-gradient(135deg, #D4AF37 0%, #B8860B 100%)" if is_praying else "#1a1a1a"
        txt = "#000" if is_praying else "#D4AF37"
        
        # MAIN LIST DESIGN
        html += f"""<div style="background:{bg}; color:{txt}; padding:15px; margin-bottom:15px; border-radius:15px; border:1px solid #D4AF37; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="flex:1;">
                    <strong style="font-size:1.2em;">{p['n']}</strong><br>
                    <small style="opacity:0.8;">Shift: {p['s']}</small>
                </div>
                <div style="text-align:right; flex:1;">
                    <span style="font-weight:bold; font-size:1.1em;">{p['st']}</span><br>
                    <small>{p['in']} - {p['out']} {f'({p["dur"]})' if p["dur"] else ''}</small>
                </div>
            </div>"""
        
        # THIS PART SHOWS THE VISION ON THE MAIN SCREEN
        if p.get('v'):
            html += f"""<div style="margin-top:10px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.2); font-style:italic; font-size:0.95em;">
                <span style="font-weight:bold;">📜 Word:</span> "{p['v']}"
            </div>"""
            
        html += "</div>"
    html += "</div>"
    return html

def reset_altar(pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), "🔒 Denied"
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    save_data(data)
    return render_list(), "🔄 Altar Reset for New Day"

# --- UI DESIGN ---
with gr.Blocks(css=".gradio-container {background-color: #000; color: #D4AF37;}") as demo:
    gr.HTML(f"<div style='text-align:center; padding: 20px;'><h1 style='color: white;'>PASTORIA DAILY ALTAR</h1><p>NIGERIA TIME: {get_nigeria_time().strftime('%I:%M %p')}</p></div>")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🕯️ Live Altar Watch")
            list_view = gr.HTML(render_list())
            
        with gr.Column(scale=1):
            gr.Markdown("### ⚔️ Priest Panel")
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Select Name")
            
            with gr.Row():
                btn_in = gr.Button("🔥 START", variant="primary")
                btn_out = gr.Button("✅ FINISH")
            
            gr.Markdown("---")
            # THE VISION INPUT
            vision_box = gr.Textbox(label="Prophetic Vision / Testimony", placeholder="Type your word here...", lines=3)
            btn_vision = gr.Button("📤 SEND VISION", variant="secondary")
            
            status_msg = gr.Markdown("**Status:** Ready")

            with gr.Accordion("🛡️ Admin", open=False):
                pw = gr.Textbox(label="Admin Password", type="password")
                reset_btn = gr.Button("🔄 RESET FOR NEW DAY", variant="stop")

    # LOGIC
    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status_msg])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status_msg])
    btn_vision.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status_msg])
    reset_btn.click(reset_altar, [pw], [list_view, status_msg])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
