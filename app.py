import gradio as gr
from datetime import datetime
import json
import os
import urllib.parse
from fastapi import FastAPI

# Vercel temporary storage
DB_FILE = "/tmp/prayer_data.json"
ADMIN_PASSWORD = "Admin123" 

# --- UPDATED PRAYER DATA ---
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
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": ""})
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

def update(name, action):
    if not name: return render(), report(), ""
    t = datetime.now().strftime("%I:%M %p")
    for p in current_pastors:
        if p["n"] == name:
            if action == "in": 
                p["st"], p["in"] = "🔥 Praying", t
            else: 
                p["st"], p["out"] = "✅ Done", t
                mins = calculate_duration(p["in"], t)
                p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_pastors)
    return render(), report(), get_whatsapp_link()

def reset_all(pwd):
    global current_pastors
    if pwd != ADMIN_PASSWORD:
        return render(), "❌ INCORRECT PASSWORD", ""
    new_data = [p.copy() for p in pastors_list]
    for p in new_data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": ""})
    current_pastors = new_data
    save_data(current_pastors)
    return render(), report(), ""

def render():
    h = ""
    for p in current_pastors:
        bg = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        display_dur = f"<br><b style='color:#1b5e20;'>Duration: {p['dur']}</b>" if p['dur'] else ""
        h += f"<div style='background:{bg}; color:#000000; padding:12px; margin:8px 0; border-radius:10px; display:flex; justify-content:space-between; border: 2px solid #D4AF37; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>"
        h += f"<span><b style='font-size:1.1em; color:#000000;'>{p['n']}</b><br><small style='color:#333;'>{p['s']}</small>{display_dur}</span>"
        h += f"<span style='text-align:right;'><b style='color:#000000;'>{p['st']}</b><br><small style='color:#333;'>{p['in']} - {p['out']}</small></span></div>"
    return h

def report():
    signed_in = len([p for p in current_pastors if p['in'] != "--"])
    signed_out = len([p for p in current_pastors if p['out'] != "--"])
    total_mins = sum([calculate_duration(p["in"], p["out"]) for p in current_pastors if p["out"] != "--"])
    forgot_out = [p['n'] for p in current_pastors if p['in'] != "--" and p['out'] == "--"]
    note = f"\n\n* Note: {', '.join(forgot_out)} signed into prayers but did not sign out." if forgot_out else ""
    return (f"Prayers information\n\n"
            f"1. Numbers of pastors Signed In: {signed_in}\n"
            f"2. Numbers of pastors Signed Out: {signed_out}\n"
            f"3. Total Prayer Hours Recorded: {total_mins//60}h {total_mins%60}m\n"
            f"4. Total Prayer Time Concluded: {datetime.now().strftime('%I:%M %p')}"
            f"{note}")

def get_whatsapp_link():
    text = report()
    encoded_text = urllib.parse.quote(text)
    return f"https://wa.me/?text={encoded_text}"

# --- OVERSEER VISION FUNCTION ---
def overseer_vision(name_typed, pwd):
    if pwd != ADMIN_PASSWORD:
        return "🔒 Enter Admin Password below to activate Overseer Vision."
    if not name_typed:
        active = [p['n'] for p in current_pastors if "Praying" in p['st']]
        return f"👁️ OVERSEER WATCH: No one typing. Currently Praying: {', '.join(active) if active else 'None'}"
    return f"👁️ OVERSEER WATCH: {name_typed} is currently at the Altar (Typing/Selecting)..."

css_styling = """
.gradio-container {background-color: #000000 !important; color: #ffffff !important;}
.gr-button {font-weight: bold;}
"""

with gr.Blocks(css=css_styling) as demo:
    gr.HTML("""
        <div style="text-align: center; background: #000000; color: #D4AF37; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 20px;">
            <h1 style="margin: 0; font-weight: 900;">PASTORIA DAILY PRAYER</h1>
            <p style="margin: 5px 0; color: #ffffff;">GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
            <p style="color: #D4AF37; font-weight: bold;">ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("<h3 style='color: #D4AF37;'>Altar Watch List</h3>")
            view = gr.HTML(render())
        
        with gr.Column():
            gr.Markdown("<h3 style='color: #D4AF37;'>Priestly Sign-In</h3>")
            name = gr.Dropdown([p["n"] for p in current_pastors], label="Select Name")
            
            with gr.Row():
                i_btn = gr.Button("🔥 START PRAYER", variant="primary")
                o_btn = gr.Button("✅ FINISH PRAYER")
            
            rep = gr.Textbox(label="Report Data (Ready for WhatsApp)", value=report(), lines=10)
            
            with gr.Accordion("Admin Controls", open=False):
                gr.Markdown("### 👁️ Overseer Vision")
                vision_status = gr.Label(value="Enter Password below to activate Vision")
                gr.Markdown("---")
                wa_btn = gr.Button("📲 SHARE REPORT TO WHATSAPP", variant="primary")
                gr.Markdown("---")
                admin_pwd = gr.Textbox(label="Admin Password", type="password")
                reset_btn = gr.Button("🔄 RESET ALL DATA FOR NEW DAY", variant="stop")
            
            wa_link = gr.Markdown(visible=False)

    # Click Handlers
    i_btn.click(update, inputs=[name, gr.State("in")], outputs=[view, rep, wa_link])
    o_btn.click(update, inputs=[name, gr.State("out")], outputs=[view, rep, wa_link])
    reset_btn.click(reset_all, inputs=[admin_pwd], outputs=[view, rep, wa_link])
    
    # Vision Trigger
    name.change(overseer_vision, inputs=[name, admin_pwd], outputs=[vision_status])
    
    wa_btn.click(fn=lambda: None, js=f"window.open('{get_whatsapp_link()}', '_blank')")

# --- VERCEL BRIDGE ---
app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
