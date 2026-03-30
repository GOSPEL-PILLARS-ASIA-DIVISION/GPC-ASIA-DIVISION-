import gradio as gr
from datetime import datetime
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
# This uses the Upstash credentials from your Vercel Environment Variables
redis = Redis(
    url=os.environ.get("UPSTASH_REDIS_REST_URL"), 
    token=os.environ.get("UPSTASH_REDIS_REST_TOKEN")
)

ADMIN_PASSWORD = "Admin123" 

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

def load_data():
    try:
        raw = redis.get("asia_altar_v4")
        if raw: return json.loads(raw)
    except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "v": ""})
    return data

def save_data(data):
    redis.set("asia_altar_v4", json.dumps(data))

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "Please select a name."
    current_data = load_data()
    now_time = datetime.now().strftime("%I:%M %p")
    msg = ""
    
    for p in current_data:
        if p["n"] == name:
            if action_type == "start":
                p["st"], p["in"] = "🔥 Praying", now_time
                msg = f"Prayer started for {name}"
            elif action_type == "finish":
                p["st"], p["out"] = "✅ Done", now_time
                msg = f"Prayer finished for {name}"
            elif action_type == "vision":
                p["v"] = vision_text
                msg = f"Vision recorded for {name}!"
    
    save_data(current_data)
    return render_list(), msg

def render_list():
    current_pastors = load_data()
    html = ""
    for p in current_pastors:
        color = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        html += f"""<div style="background:{color}; color:#000; padding:12px; margin:8px; border-radius:10px; border:2px solid #D4AF37; display:flex; justify-content:space-between; align-items:center; font-weight:bold;">
            <div>{p['n']}<br><small>{p['s']}</small></div>
            <div style="text-align:right;">{p['st']}<br><small>{p['in']} - {p['out']}</small></div>
        </div>"""
    return html

def admin_view(pwd):
    if pwd != ADMIN_PASSWORD: return "🔒 Access Denied"
    current_data = load_data()
    visions = "### 📜 Prophetic Visions Log:\n\n"
    found = False
    for p in current_data:
        if p.get('v'):
            visions += f"**{p['n']}:** {p['v']}\n\n---\n"
            found = True
    return visions if found else "No visions recorded yet."

# --- UI DESIGN ---
with gr.Blocks(css=".gradio-container {background-color: #000; color: #D4AF37;}") as demo:
    gr.HTML("<h1 style='text-align:center; color:white;'>PASTORIA DAILY PRAYER</h1>")
    
    with gr.Row():
        with gr.Column(scale=1):
            list_view = gr.HTML(render_list())
            
        with gr.Column(scale=1):
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Select Your Name")
            
            with gr.Group():
                gr.Markdown("### **1. Altar Entrance**")
                with gr.Row():
                    btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                    btn_out = gr.Button("✅ FINISH PRAYER")
            
            gr.Markdown("---")
            
            with gr.Group():
                gr.Markdown("### **2. Prophetic Record**")
                vision_box = gr.Textbox(label="Write Vision/Word", placeholder="What is the Spirit saying?", lines=3)
                btn_vision = gr.Button("📤 SEND VISION TO ALTAR", variant="secondary")
            
            status_msg = gr.Markdown("Status: Ready")

            with gr.Accordion("🛡️ Admin Panel", open=False):
                pw = gr.Textbox(label="Password", type="password")
                v_log = gr.Markdown("Visions are hidden.")
                v_btn = gr.Button("VIEW ALL VISIONS")

    # Button Logic
    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status_msg])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status_msg])
    btn_vision.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status_msg])
    v_btn.click(admin_view, [pw], [v_log])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
