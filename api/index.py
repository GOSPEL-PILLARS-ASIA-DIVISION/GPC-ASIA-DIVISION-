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

# --- ASIA TIME OFFSET ---
# If you are in Singapore/Philippines/Malaysia, use 8. 
# If you are in Thailand/Vietnam, use 7.
ASIA_OFFSET = 8 

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

def get_asia_time():
    # Adjusts the server time to Asia Time
    return datetime.utcnow() + timedelta(hours=ASIA_OFFSET)

def load_data():
    try:
        raw = redis.get("asia_altar_final")
        if raw: return json.loads(raw)
    except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    redis.set("asia_altar_final", json.dumps(data))

def calculate_duration(start_str, end_str):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_str, fmt)
        t2 = datetime.strptime(end_str, fmt)
        # Handle crossing midnight
        if t2 < t1: t2 += timedelta(days=1)
        diff = t2 - t1
        mins = int(diff.total_seconds() / 60)
        return f"{mins//60}h {mins%60}m"
    except: return ""

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select a name first!"
    current_data = load_data()
    now_time = get_asia_time().strftime("%I:%M %p")
    msg = ""
    
    for p in current_data:
        if p["n"] == name:
            if action_type == "start":
                p["st"], p["in"], p["out"], p["dur"] = "🔥 Praying", now_time, "--", ""
                msg = f"🙏 {name} started at {now_time}"
            elif action_type == "finish":
                if p["in"] == "--": return render_list(), "⚠️ You must START first!"
                p["st"], p["out"] = "✅ Done", now_time
                p["dur"] = calculate_duration(p["in"], now_time)
                msg = f"🙌 {name} finished! Total: {p['dur']}"
            elif action_type == "vision":
                p["v"] = vision_text
                msg = f"✍️ Vision saved for {name}!"
    
    save_data(current_data)
    return render_list(), msg

def render_list():
    current_pastors = load_data()
    html = "<div style='max-height: 400px; overflow-y: auto;'>"
    for p in current_pastors:
        # Highlight row if praying
        bg = "linear-gradient(90deg, #D4AF37, #FFD700)" if "Praying" in p["st"] else "#1a1a1a"
        text = "#000" if "Praying" in p["st"] else "#D4AF37"
        
        html += f"""<div style="background:{bg}; color:{text}; padding:15px; margin-bottom:10px; border-radius:12px; border:1px solid #D4AF37; display:flex; justify-content:space-between; align-items:center; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
            <div style="flex:1;">
                <strong style="font-size:1.1em;">{p['n']}</strong><br>
                <small style="opacity:0.8;">Schedule: {p['s']}</small>
            </div>
            <div style="text-align:right; flex:1;">
                <span style="font-weight:bold;">{p['st']}</span><br>
                <small>{p['in']} - {p['out']} {f'({p["dur"]})' if p["dur"] else ''}</small>
            </div>
        </div>"""
    html += "</div>"
    return html

def admin_view(pwd):
    if pwd != ADMIN_PASSWORD: return "🔒 Access Denied"
    current_data = load_data()
    visions = "### 📜 PROPHETIC RECORD\n\n"
    for p in current_data:
        if p.get('v'): visions += f"**{p['n']}:** {p['v']}\n\n---\n"
    return visions

# --- UI DESIGN ---
with gr.Blocks(css=".gradio-container {background-color: #000; color: #D4AF37; font-family: 'Arial';}") as demo:
    gr.HTML("""
    <div style='text-align:center; padding: 20px; border-bottom: 2px solid #D4AF37;'>
        <h1 style='color: white; margin:0;'>PASTORIA DAILY ALTAR</h1>
        <p style='color: #D4AF37; margin:5px;'>ASIA DIVISION RECORD</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🕯️ Live Altar Status")
            list_view = gr.HTML(render_list())
            
        with gr.Column(scale=1):
            gr.Markdown("### ✍️ Priest Actions")
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Choose Your Name")
            
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            
            gr.Markdown("---")
            vision_box = gr.Textbox(label="Prophetic Vision / Word", placeholder="Type what you see in the Spirit...", lines=4)
            btn_vision = gr.Button("📤 SEND VISION TO ALTAR", variant="secondary")
            
            status_msg = gr.Markdown("**Status:** Awaiting input...")

            with gr.Accordion("🛡️ Admin Center", open=False):
                pw = gr.Textbox(label="Password", type="password")
                v_log = gr.Markdown("Visions are encrypted.")
                v_btn = gr.Button("VIEW ALL VISIONS")

    # Button Logic
    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status_msg])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status_msg])
    btn_vision.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status_msg])
    v_btn.click(admin_view, [pw], [v_log])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
