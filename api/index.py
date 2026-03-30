import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- DATABASE CONNECTION ---
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
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
        raw = redis.get("altar_v8_visible")
        if raw: return json.loads(raw)
    except: pass
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    return data

def save_data(data):
    try: redis.set("altar_v8_visible", json.dumps(data))
    except: pass

def calculate_duration(start_str, end_str):
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_str, fmt)
        t2 = datetime.strptime(end_str, fmt)
        if t2 <= t1: t2 += timedelta(days=1)
        diff = t2 - t1
        mins = int(diff.total_seconds() / 60)
        return f"{mins//60}h {mins%60}m"
    except: return "0h 0m"

def handle_action(name, action_type, vision_text=""):
    if not name: return render_list(), "⚠️ Select Name"
    current_data = load_data()
    now_time = get_now().strftime("%I:%M %p")
    for p in current_data:
        if p["n"] == name:
            if action_type == "start": p.update({"st": "🔥 PRAYING", "in": now_time, "out": "--", "dur": ""})
            elif action_type == "finish":
                if p["in"] == "--": continue
                p.update({"st": "✅ DONE", "out": now_time, "dur": calculate_duration(p["in"], now_time)})
            elif action_type == "vision": p["v"] = vision_text
    save_data(current_data)
    return render_list(), f"Recorded at {now_time}"

def render_list():
    current_pastors = load_data()
    html = "<div style='max-height: 500px; overflow-y: auto; padding: 10px;'>"
    for p in current_pastors:
        is_praying = "PRAYING" in p["st"]
        # High contrast colors: Gold for active, Dark Grey for waiting
        bg = "#D4AF37" if is_praying else "#2d2d2d" 
        txt = "#000000" if is_praying else "#FFFFFF" # Black text on gold, White text on grey
        
        html += f"""<div style="background:{bg}; color:{txt}; padding:15px; margin-bottom:12px; border-radius:10px; border:2px solid #D4AF37;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b style="font-size:1.2em; text-transform: uppercase;">{p['n']}</b>
                <b style="font-size:1.0em;">{p['st']}</b>
            </div>
            <div style="margin-top:5px; font-weight: 500;">
                Shift: {p['s']} | Time: {p['in']} - {p['out']} {f'({p["dur"]})' if p["dur"] else ''}
            </div>"""
        if p.get('v'):
            html += f"<div style='margin-top:10px; border-top:1px solid {txt}; padding-top:8px; font-style:italic;'>📜 Vision: {p['v']}</div>"
        html += "</div>"
    html += "</div>"
    return html

def reset_altar(pwd):
    if pwd != ADMIN_PASSWORD: return render_list(), "❌ Denied"
    data = [p.copy() for p in pastors_list]
    for p in data: p.update({"st": "Waiting", "in": "--", "out": "--", "dur": "", "v": ""})
    save_data(data)
    return render_list(), "🔄 Reset Complete"

with gr.Blocks(css=".gradio-container {background-color:#121212;} .primary-btn {background-color:#D4AF37 !important;}") as demo:
    gr.HTML("<div style='text-align:center; padding:10px;'><h1 style='color:#D4AF37; margin:0;'>NIGERIA SPIRITUAL ALTAR</h1><p style='color:white;'>OFFICIAL PRAYER WATCH</p></div>")
    
    with gr.Row():
        with gr.Column(scale=1):
            list_view = gr.HTML(render_list())
        with gr.Column(scale=1):
            name_sel = gr.Dropdown([p["n"] for p in pastors_list], label="Identify Yourself")
            with gr.Row():
                btn_in = gr.Button("🔥 START PRAYER", variant="primary")
                btn_out = gr.Button("✅ FINISH PRAYER")
            vision_box = gr.Textbox(label="Prophetic Vision", placeholder="Write word here...", lines=3)
            btn_v = gr.Button("📤 SEND VISION")
            status = gr.Markdown("🟢 System Online")
            with gr.Accordion("🛡️ Admin", open=False):
                pw = gr.Textbox(label="Password", type="password")
                reset_btn = gr.Button("RESET DAY")

    btn_in.click(handle_action, [name_sel, gr.State("start")], [list_view, status])
    btn_out.click(handle_action, [name_sel, gr.State("finish")], [list_view, status])
    btn_v.click(handle_action, [name_sel, gr.State("vision"), vision_box], [list_view, status])
    reset_btn.click(reset_altar, [pw], [list_view, status])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
