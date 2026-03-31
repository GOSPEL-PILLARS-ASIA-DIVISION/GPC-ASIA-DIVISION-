import gradio as gr
from datetime import datetime
import json
import os
import urllib.parse
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
REDIS_URL = os.environ.get("REDIS_URL")
REDIS_TOKEN = os.environ.get("REDIS_TOKEN")
redis = Redis(url=REDIS_URL, token=REDIS_TOKEN) if REDIS_URL else None

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

# --- STORAGE FUNCTIONS ---
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

def load_visions():
    if redis:
        try:
            raw = redis.get("altar_visions")
            return json.loads(raw) if raw else []
        except: pass
    return []

def save_vision(text, name):
    if not text or not name: return "⚠️ Select name and write vision."
    visions = load_visions()
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    visions.append({"n": name, "t": text, "d": timestamp})
    if redis: redis.set("altar_visions", json.dumps(visions))
    return "✅ Vision submitted to Altar."

# --- LOGIC FUNCTIONS ---
def calculate_duration(start_t, end_t):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_t, fmt)
        t2 = datetime.strptime(end_t, fmt)
        diff = (t2 - t1).total_seconds()
        if diff < 0: diff += 86400
        return int(diff / 60)
    except: return 0

def get_report(current_data):
    signed_in = len([p for p in current_data if p['in'] != "--"])
    signed_out = len([p for p in current_data if p['out'] != "--"])
    total_mins = sum([calculate_duration(p["in"], p["out"]) for p in current_data if p["out"] != "--"])
    return (f"Prayers information\n\n1. Signed In: {signed_in}\n2. Signed Out: {signed_out}\n"
            f"3. Total Hours: {total_mins//60}h {total_mins%60}m\n4. Time: {datetime.now().strftime('%I:%M %p')}")

def update(name, action):
    current_data = load_data()
    if not name: return render_html(current_data), get_report(current_data), ""
    t = datetime.now().strftime("%I:%M %p")
    for p in current_data:
        if p["n"] == name:
            if action == "in": p.update({"st": "🔥 Praying", "in": t, "out": "--", "dur": ""})
            else: 
                p["st"], p["out"] = "✅ Done", t
                mins = calculate_duration(p["in"], t)
                p["dur"] = f"{mins//60}h {mins%60}m"
    save_data(current_data)
    rep = get_report(current_data)
    return render_html(current_data), rep, f"https://wa.me/?text={urllib.parse.quote(rep)}"

def view_visions_admin(pwd):
    if pwd != ADMIN_PASSWORD: return "❌ Incorrect Password"
    visions = load_visions()
    if not visions: return "No visions recorded yet."
    output = "--- ALTAR VISIONS (ADMIN ONLY) ---\n"
    for v in visions:
        output += f"[{v['d']}] {v['n']}: {v['t']}\n\n"
    return output

def reset_all(pwd):
    if pwd != ADMIN_PASSWORD: return render_html(load_data()), "❌ INCORRECT PASSWORD", ""
    new_data = [p.copy() for p in pastors_list]
    for p in new_data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": ""})
    save_data(new_data)
    if redis: redis.delete("altar_visions")
    return render_html(new_data), get_report(new_data), ""

def render_html(current_data):
    h = ""
    for p in current_data:
        bg = "#D4AF37" if "Praying" in p["st"] else "#ffffff"
        h += f"<div style='background:{bg}; color:#000; padding:12px; margin:8px 0; border-radius:10px; border: 2px solid #D4AF37; display:flex; justify-content:space-between;'>"
        h += f"<span><b>{p['n']}</b><br><small>{p['s']}</small></span>"
        h += f"<span style='text-align:right;'><b>{p['st']}</b><br><small>{p['in']} - {p['out']}</small></span></div>"
    return h

# --- UI DESIGN ---
css_styling = ".gradio-container {background-color: #000 !important; color: #fff !important;}"

with gr.Blocks(css=css_styling) as demo:
    gr.HTML("""<div style="text-align: center; background: #000; color: #D4AF37; padding: 20px; border-radius: 15px; border: 3px solid #D4AF37; margin-bottom: 20px;">
            <h1 style="margin: 0; font-weight: 900; color: white !important;">PASTORIA DAILY PRAYER</h1>
            <p style="margin: 5px 0; color: #ffffff;">GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
            <p style="color: #D4AF37; font-weight: bold; text-transform: uppercase;">ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
        </div>""")
    
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
            
            gr.Markdown("---")
            gr.Markdown("<h3 style='color: #D4AF37;'>Vision Altar</h3>")
            vision_input = gr.Textbox(label="Write your vision here (Only Admin can see)", placeholder="Type vision...")
            v_btn = gr.Button("📝 SUBMIT VISION")
            v_msg = gr.Markdown("")

            rep = gr.Textbox(label="Report Data", value=get_report(load_data()), lines=5)
            
            with gr.Accordion("Admin Controls", open=False):
                wa_btn = gr.Button("📲 OPEN WHATSAPP LINK", variant="primary")
                admin_pwd = gr.Textbox(label="Admin Password", type="password")
                view_v_btn = gr.Button("👁️ VIEW ALL VISIONS")
                visions_display = gr.Textbox(label="Vision Records", lines=10)
                reset_btn = gr.Button("🔄 RESET ALL DATA", variant="stop")
            
            wa_link = gr.Markdown(visible=False)

    # Click Handlers
    i_btn.click(update, inputs=[name, gr.State("in")], outputs=[view, rep, wa_link])
    o_btn.click(update, inputs=[name, gr.State("out")], outputs=[view, rep, wa_link])
    v_btn.click(save_vision, inputs=[vision_input, name], outputs=[v_msg]).then(lambda: "", None, vision_input)
    view_v_btn.click(view_visions_admin, inputs=[admin_pwd], outputs=[visions_display])
    reset_btn.click(reset_all, inputs=[admin_pwd], outputs=[view, rep, wa_link])
    wa_btn.click(fn=None, inputs=wa_link, js="(link) => { if(link) window.open(link, '_blank'); }")

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
