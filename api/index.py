import gradio as gr
from datetime import datetime
import json
import os
from fastapi import FastAPI

# Vercel uses /tmp for temporary session storage
DB_FILE = "/tmp/prayer_data.json"
ADMIN_PASSWORD = "Admin123" 

# --- ASIA DIVISION PASTOR LIST ---
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

def update_altar(name, vision_text, action):
    if not name: return render_list(), report_logic()
    now_time = datetime.now().strftime("%I:%M %p")
    for p in current_pastors:
        if p["n"] == name:
            if action == "start":
                p["st"], p["in"], p["v"] = "🔥 Praying", now_time, vision_text
            else:
                p["st"], p["out"] = "✅ Done", now_time
                mins = calculate_duration(p["in"], now_time)
                p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_pastors)
    return render_list(), report_logic()

def manual_signout(name, pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), report_logic()
    if not name: return render_list(), report_logic()
    now_time = datetime.now().strftime("%I:%M %p")
    for p in current_pastors:
        if p["n"] == name and p["st"] == "🔥 Praying":
            p["st"], p["out"] = "✅ Done (Admin Force)", now_time
            mins = calculate_duration(p["in"], now_time)
            p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_pastors)
    return render_list(), report_logic()

def report_logic():
    s_in = [p for p in current_pastors if p['in'] != "--"]
    s_out = [p for p in current_pastors if p['out'] != "--"]
    forgot_out = [p['n'] for p in current_pastors if p['in'] != "--" and p['out'] == "--"]
    total_mins = sum([calculate_duration(p["in"], p["out"]) for p in s_out])
    note = f"\n⚠️ ALERT: {', '.join(forgot_out)} did not sign out." if forgot_out else "\n✨ All signed out."
    return (f"PRAYER ALTAR REPORT\n"
            f"1. Signed In: {len(s_in)}\n2. Signed Out: {len(s_out)}\n"
            f"3. Total Time: {total_mins//60}h {total_mins%60}m\n"
            f"4. Time: {datetime.now().strftime('%I:%M %p')}\n{note}")

def render_list():
    html = ""
    for p in current_pastors:
        color = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        html += f"""<div style="background:{color}; color:#000; padding:10px; margin:5px; border-radius:8px; border:2px solid #D4AF37; display:flex; justify-content:space-between;">
            <div><b>{p['n']}</b><br><small>{p['s']}</small></div>
            <div style="text-align:right;"><b>{p['st']}</b><br><small>{p['in']} - {p['out']}</small></div>
        </div>"""
    return html

def admin_view(pwd):
    if pwd != ADMIN_PASSWORD: return "🔒 Access Denied"
    visions = "### 📜 Prophetic Visions:\n"
    for p in current_pastors:
        if p['v']: visions += f"**{p['n']}:** {p['v']}\n\n"
    return visions or "No visions yet."

def reset_app(pwd):
    global current_pastors
    if pwd != ADMIN_PASSWORD: return render_list(), report_logic()
    current_pastors = load_data()
    save_data(current_pastors)
    return render_list(), report_logic()

# --- THE UI ---
css = ".gradio-container {background-color: #000 !important; color: #D4AF37 !important;}"
with gr.Blocks(css=css) as demo:
    gr.HTML("<div style='text-align:center; padding:20px;'><h1 style='color:#D4AF37;'>PASTORIA PRAYER TRACKER</h1><p style='color:white;'>Gospel Pillars Asia Division</p></div>")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔥 Live Altar Watch")
            list_view = gr.HTML(render_list())
        with gr.Column(scale=1):
            gr.Markdown("### ✍️ Priestly Sign-In")
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Select Your Name")
            
            # --- UPDATED WRITE YOUR VISION LABEL ---
            vision_box = gr.Textbox(label="Write your vision", placeholder="What is the Spirit saying?", lines=3)
            
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            
            with gr.Accordion("🛡️ Admin Command Center", open=False):
                pass_box = gr.Textbox(label="Admin Password", type="password")
                with gr.Tab("Manual Tools"):
                    admin_target = gr.Dropdown([p["n"] for p in pastors_list], label="Force Sign-Out For:")
                    force_btn = gr.Button("⛔ FORCE OUT")
                with gr.Tab("Prophetic Logs"):
                    vision_log = gr.Markdown("Visions are hidden.")
                    view_v_btn = gr.Button("👁️ VIEW VISIONS")
                with gr.Tab("Report & Reset"):
                    report_box = gr.Textbox(label="Current Report", value=report_logic(), lines=5)
                    wa_btn = gr.Button("📲 SHARE TO WHATSAPP", variant="primary")
                    reset_btn = gr.Button("🔄 RESET FOR NEW DAY", variant="stop")

    # App Actions
    btn_in.click(update_altar, [name_sel, vision_box, gr.State("start")], [list_view, report_box])
    btn_out.click(update_altar, [name_sel, vision_box, gr.State("finish")], [list_view, report_box])
    view_v_btn.click(admin_view, [pass_box], [vision_log])
    force_btn.click(manual_signout, [admin_target, pass_box], [list_view, report_box])
    reset_btn.click(reset_app, [pass_box], [list_view, report_box])
    wa_btn.click(fn=None, inputs=report_box, js="(report) => { window.open('https://wa.me/?text=' + encodeURIComponent(report), '_blank'); }")

# --- VERCEL FASTAPI BRIDGE ---
app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
