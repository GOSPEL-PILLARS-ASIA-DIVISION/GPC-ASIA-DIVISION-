import gradio as gr
from datetime import datetime, timedelta
import json
import os
import urllib.parse
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION (Required for GitHub/Vercel Persistence) ---
REDIS_URL = os.environ.get("REDIS_URL")
REDIS_TOKEN = os.environ.get("REDIS_TOKEN")
redis = Redis(url=REDIS_URL, token=REDIS_TOKEN) if REDIS_URL else None

ADMIN_PASSWORD = "Admin123" 

# --- PRAYER DATA ---
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
    if redis:
        try:
            raw = redis.get("prayer_altar_db")
            if raw: return json.loads(raw)
        except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": ""})
    return data

def save_data(data):
    if redis:
        try: redis.set("prayer_altar_db", json.dumps(data))
        except: pass

def calculate_duration(start_t, end_t):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_t, fmt)
        t2 = datetime.strptime(end_t, fmt)
        diff = (t2 - t1).total_seconds()
        if diff < 0: diff += 86400 # Over midnight fix
        return int(diff / 60)
    except: return 0

def get_report(current_data):
    signed_in = len([p for p in current_data if p['in'] != "--"])
    signed_out = len([p for p in current_data if p['out'] != "--"])
    total_mins = sum([calculate_duration(p["in"], p["out"]) for p in current_data if p["out"] != "--"])
    forgot_out = [p['n'] for p in current_data if p['in'] != "--" and p['out'] == "--"]
    note = f"\n\n* Note: {', '.join(forgot_out)} did not sign out." if forgot_out else ""
    return (f"Prayers information\n\n"
            f"1. Pastors Signed In: {signed_in}\n"
            f"2. Pastors Signed Out: {signed_out}\n"
            f"3. Total Prayer Hours: {total_mins//60}h {total_mins%60}m\n"
            f"4. Recorded at: {datetime.now().strftime('%I:%M %p')}"
            f"{note}")

def update(name, action):
    current_data = load_data()
    if not name: return render_html(current_data), get_report(current_data), ""
    t = datetime.now().strftime("%I:%M %p")
    for p in current_data:
        if p["n"] == name:
            if action == "in": 
                p.update({"st": "🔥 Praying", "in": t, "out": "--", "dur": ""})
            else: 
                p["st"], p["out"] = "✅ Done", t
                mins = calculate_duration(p["in"], t)
                p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_data)
    rep = get_report(current_data)
    return render_html(current_data), rep, f"https://wa.me/?text={urllib.parse.quote(rep)}"

def reset_all(pwd):
    if pwd != ADMIN_PASSWORD:
        current_data = load_data()
        return render_html(current_data), "❌ INCORRECT PASSWORD", ""
    new_data = [p.copy() for p in pastors_list]
    for p in new_data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": ""})
    save_data(new_data)
    return render_html(new_data), get_report(new_data), ""

def render_html(current_data):
    h = ""
    for p in current_data:
        bg = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        display_dur = f"<br><b style='color:#b71c1c;'>Duration: {p['dur']}</b>" if p['dur'] else ""
        h += f"<div style='background:{bg}; color:#000000; padding:12px; margin:8px 0; border-radius:10px; display:flex; justify-content:space-between; border: 2px solid #D4AF37;'>"
        h += f"<span><b style='font-size:1.1em;'>{p['n']}</b><br><small>{p['s']}</small>{display_dur}</span>"
        h += f"<span style='text-align:right;'><b>{p['st']}</b><br><small>{p['in']} - {p['out']}</small></span></div>"
    return h

css_styling = """
.gradio-container {background-color: #000000 !important; color: #ffffff !important;}
.gr-button {font-weight: bold;}
"""

with gr.Blocks(css=css_styling) as demo:
    gr.HTML("""
        <div style="text-align: center; background: #000000; color: #D4AF37; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 20px;">
            <h1 style="margin: 0; font-weight: 900; color: white !important;">PASTORIA DAILY PRAYER</h1>
            <p style="margin: 5px 0; color: #ffffff;">GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
            <p style="color: #D4AF37; font-weight: bold; text-transform: uppercase;">ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("<h3 style='color: #D4AF37;'>Altar Watch List</h3>")
            view = gr.HTML(render_html(load_data()))
        
        with gr.Column():
            gr.Markdown("<h3 style='color: #D4AF37;'>Priestly Sign-In</h3>")
            name = gr.Dropdown([p["n"] for p in pastors_list], label="Select Name")
            
            with gr.Row():
                i_btn = gr.Button("🔥 START PRAYER", variant="primary")
                o_btn = gr.Button("✅ FINISH PRAYER")
            
            rep = gr.Textbox(label="Report Data", value=get_report(load_data()), lines=8)
            
            with gr.Accordion("Admin Controls", open=False):
                wa_btn = gr.Button("📲 OPEN WHATSAPP LINK", variant="primary")
                admin_pwd = gr.Textbox(label="Admin Password", type="password")
                reset_btn = gr.Button("🔄 RESET ALL DATA", variant="stop")
            
            wa_link = gr.Markdown(visible=False)

    i_btn.click(update, inputs=[name, gr.State("in")], outputs=[view, rep, wa_link])
    o_btn.click(update, inputs=[name, gr.State("out")], outputs=[view, rep, wa_link])
    reset_btn.click(reset_all, inputs=[admin_pwd], outputs=[view, rep, wa_link])
    wa_btn.click(fn=None, inputs=wa_link, js="(link) => { if(link) window.open(link, '_blank'); }")

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
