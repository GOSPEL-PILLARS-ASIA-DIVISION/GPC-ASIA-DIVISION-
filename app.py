import gradio as gr
from datetime import datetime
import json
import os
import urllib.parse
from fastapi import FastAPI

# Vercel uses /tmp for temporary session storage
DB_FILE = "/tmp/prayer_data.json"
ADMIN_PASSWORD = "Admin123" 

# --- YOUR ORIGINAL PASTOR LIST ---
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
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

current_pastors = load_data()

def calculate_duration(start_t, end_t):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_t, fmt)
        t2 = datetime.strptime(end_t, fmt)
        diff = (t2.replace(day=2) - t1.replace(day=1)).total_seconds() if t2 < t1 else (t2 - t1).total_seconds()
        return int(diff / 60)
    except: return 0

def update(name, vision_input, action):
    if not name: return render(), render_admin(""), report(), ""
    t = datetime.now().strftime("%I:%M %p")
    for p in current_pastors:
        if p["n"] == name:
            if action == "in": 
                p["st"], p["in"], p["v"] = "🔥 Praying", t, vision_input
            else: 
                p["st"], p["out"] = "✅ Done", t
                mins = calculate_duration(p["in"], t)
                p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_pastors)
    return render(), render_admin(""), report(), get_whatsapp_link()

def reset_all(pwd):
    global current_pastors
    if pwd != ADMIN_PASSWORD: return render(), "❌ INCORRECT PASSWORD", report(), ""
    new_data = [p.copy() for p in pastors_list]
    for p in new_data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    current_pastors = new_data
    save_data(current_pastors)
    return render(), render_admin(pwd), report(), ""

def render():
    h = ""
    for p in current_pastors:
        bg = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        display_dur = f"<br><b style='color:#1b5e20;'>Duration: {p['dur']}</b>" if p['dur'] else ""
        h += f"<div style='background:{bg}; color:#000; padding:12px; margin:8px 0; border-radius:10px; display:flex; justify-content:space-between; border: 2px solid #D4AF37;'>"
        h += f"<span><b style='font-size:1.1em;'>{p['n']}</b><br><small>{p['s']}</small>{display_dur}</span>"
        h += f"<span style='text-align:right;'><b>{p['st']}</b><br><small>{p['in']} - {p['out']}</small></span></div>"
    return h

def render_admin(pwd):
    if pwd != ADMIN_PASSWORD: return ""
    h = "<div style='background:#111; padding:10px; border-radius:5px; margin-top:10px;'><h4 style='color:#D4AF37;'>Vision Log:</h4>"
    for p in current_pastors:
        if p['v']: h += f"<p style='color:white;'><b>{p['n']}:</b> {p['v']}</p>"
    return h + "</div>"

def report():
    s_in = len([p for p in current_pastors if p['in'] != "--"])
    s_out = len([p for p in current_pastors if p['out'] != "--"])
    return f"Prayers information\n\n1. Signed In: {s_in}\n2. Signed Out: {s_out}\nTime: {datetime.now().strftime('%I:%M %p')}"

def get_whatsapp_link():
    return f"https://wa.me/?text={urllib.parse.quote(report())}"

# --- INTERFACE ---
with gr.Blocks(css=".gradio-container {background-color: #000 !important; color: #fff !important;}") as demo:
    gr.HTML("""
        <div style="text-align: center; background: #000; color: #D4AF37; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 20px;">
            <h1 style="margin: 0; font-weight: 900;">PASTORIA DAILY PRAYER</h1>
            <p style="margin: 5px 0; color: #fff;">GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
            <p style="color: #D4AF37; font-weight: bold;">ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🔥 Altar Watch List")
            view = gr.HTML(render())
        with gr.Column():
            gr.Markdown("### ✍️ Priestly Sign-In")
            name = gr.Dropdown([p["n"] for p in current_pastors], label="Select Name")
            vision = gr.Textbox(label="Vision / Comment", placeholder="Enter vision (Private)...")
            with gr.Row():
                i_btn = gr.Button("🔥 START PRAYER", variant="primary")
                o_btn = gr.Button("✅ FINISH PRAYER")
            rep = gr.Textbox(label="Report Data", value=report(), lines=4)
            with gr.Accordion("Admin Controls", open=False):
                admin_pwd = gr.Textbox(label="Admin Password", type="password")
                reveal_btn = gr.Button("👁️ VIEW VISIONS")
                admin_vision_view = gr.HTML("")
                wa_btn = gr.Button("📲 SHARE TO WHATSAPP", variant="primary")
                reset_btn = gr.Button("🔄 RESET DATA", variant="stop")
            wa_link = gr.Markdown(visible=False)

    i_btn.click(update, inputs=[name, vision, gr.State("in")], outputs=[view, admin_vision_view, rep, wa_link])
    o_btn.click(update, inputs=[name, vision, gr.State("out")], outputs=[view, admin_vision_view, rep, wa_link])
    reveal_btn.click(render_admin, inputs=[admin_pwd], outputs=[admin_vision_view])
    reset_btn.click(reset_all, inputs=[admin_pwd], outputs=[view, admin_vision_view, rep, wa_link])
    wa_btn.click(fn=lambda: None, js=f"window.open('{get_whatsapp_link()}', '_blank')")

# VERCEL BRIDGE
app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
