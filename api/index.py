import gradio as gr
from datetime import datetime
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
# Vercel automatically provides KV_REST_API_URL and KV_REST_API_TOKEN 
# once you click "Connect" in the Storage tab.
redis = Redis.from_env()

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
    # Try to get data from permanent Redis storage
    raw_data = redis.get("altar_data")
    if raw_data:
        return json.loads(raw_data)
    
    # If no data exists (first time), create it
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    # Save to permanent Redis storage
    redis.set("altar_data", json.dumps(data))

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
    current_pastors = load_data()
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
    current_pastors = load_data()
    now_time = datetime.now().strftime("%I:%M %p")
    for p in current_pastors:
        if p["n"] == name and p["st"] == "🔥 Praying":
            p["st"], p["out"] = "✅ Done (Admin Force)", now_time
            mins = calculate_duration(p["in"], now_time)
            p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_pastors)
    return render_list(), report_logic()

def report_logic():
    current_pastors = load_data()
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
    current_pastors = load_data()
    html = ""
    for p in current_pastors:
        color = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        html += f"""<div style="background:{color}; color:#000; padding:12px; margin:8px; border-radius:10px; border:2px solid #D4AF37; display:flex; justify-content:space-between; align-items:center; font-weight:bold;">
            <div><span style="font-size:1.1em;">{p['n']}</span><br><small style="font-weight:normal; color:#444;">{p['s']}</small></div>
            <div style="text-align:right;"><span>{p['st']}</span><br><small style="font-weight:normal; color:#444;">{p['in']} - {p['out']}</small></div>
        </div>"""
    return html

def admin_view(pwd):
    if pwd != ADMIN_PASSWORD: return "🔒 Access Denied"
    current_pastors = load_data()
    visions = "### 📜 Prophetic Visions:\n"
    for p in current_pastors:
        if p['v']: visions += f"**{p['n']}:** {p['v']}\n\n"
    return visions or "No visions yet recorded."

def reset_app(pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), report_logic()
    # Completely clear Redis and restart
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    save_data(data)
    return render_list(), report_logic()

# --- THE UI ---
css = ".gradio-container {background-color: #000 !important; color: #D4AF37 !important;}"
with gr.Blocks(css=css) as demo:
    gr.HTML("""
    <div style='text-align:center; border: 3px solid #D4AF37; border-radius: 20px; padding: 25px; margin: 15px auto; max-width: 600px; background-color: #000;'>
        <h1 style='color: white; font-size: 2.2em; margin-bottom: 5px; font-weight: bold;'>PASTORIA DAILY PRAYER</h1>
        <p style='color: white; font-size: 1.1em; margin: 0; letter-spacing: 1px;'>GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
        <p style='color: #D4AF37; font-size: 1em; margin-top: 15px; font-weight: bold;'>ASIA DIVISION HEAD | APOSTEL SOLOMON SUCCESS</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### **Altar Watch List**")
            list_view = gr.HTML(render_list())
        with gr.Column(scale=1):
            gr.Markdown("### **Priestly Sign-In**")
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Select Your Name")
            vision_box = gr.Textbox(label="Write your vision", placeholder="What is the Spirit saying?", lines=3)
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            
            with gr.Accordion("🛡️ Admin Center", open=False):
                pass_box = gr.Textbox(label="Admin Password", type="password")
                with gr.Tab("Tools"):
                    admin_target = gr.Dropdown([p["n"] for p in pastors_list], label="Force Sign-Out For:")
                    force_btn = gr.Button("⛔ FORCE OUT")
                with gr.Tab("Visions"):
                    vision_log = gr.Markdown("Visions are private.")
                    view_v_btn = gr.Button("👁️ VIEW")
                with gr.Tab("Report"):
                    report_box = gr.Textbox(label="Report", value=report_logic(), lines=5)
                    wa_btn = gr.Button("📲 WHATSAPP", variant="primary")
                    reset_btn = gr.Button("🔄 RESET DAY", variant="stop")

    # Actions
    btn_in.click(update_altar, [name_sel, vision_box, gr.State("start")], [list_view, report_box])
    btn_out.click(update_altar, [name_sel, vision_box, gr.State("finish")], [list_view, report_box])
    view_v_btn.click(admin_view, [pass_box], [vision_log])
    force_btn.click(manual_signout, [admin_target, pass_box], [list_view, report_box])
    reset_btn.click(reset_app, [pass_box], [list_view, report_box])
    wa_btn.click(fn=None, inputs=report_box, js="(report) => { window.open('https://wa.me/?text=' + encodeURIComponent(report), '_blank'); }")

# --- VERCEL BRIDGE ---
app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
