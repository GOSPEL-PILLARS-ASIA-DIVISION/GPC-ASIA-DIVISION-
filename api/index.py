import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- FAST DATABASE LINK ---
# Initializing once outside the functions saves time
redis = Redis(url=os.environ.get("UPSTASH_REDIS_REST_URL"), token=os.environ.get("UPSTASH_REDIS_REST_TOKEN"))

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

def load_db():
    try:
        raw = redis.get("asia_v60_speed")
        if raw: return json.loads(raw)
    except: pass
    return [{"n": p["n"], "s": p["s"], "st": "Waiting", "in": "--", "out": "--"} for p in pastors_list]

def render():
    data = load_db()
    html = "<div style='background:#000; padding:10px;'>"
    for p in data:
        is_p = "Praying" in p["st"]
        bg = "#D4AF37" if is_p else "#FFF"
        html += f"""<div style="background:{bg}; border:2px solid #D4AF37; padding:12px; margin-bottom:8px; border-radius:12px; color:#000;">
            <div style="display:flex; justify-content:space-between;"><b>{p['n']}</b> <b>{'🔥 ' if is_p else ''}{p['st']}</b></div>
            <div style="font-size:0.8em; opacity:0.8;">{p['s']} | {p['in']} - {p['out']}</div>
        </div>"""
    return html + "</div>"

def act(name, m):
    if not name: return render(), "⚠️ Select Name"
    db = load_db()
    now = (datetime.utcnow() + timedelta(hours=1)).strftime("%I:%M %p")
    for p in db:
        if p["n"] == name:
            p["st"] = "Praying" if m == "s" else "✅ Done"
            if m == "s": p["in"], p["out"] = now, "--"
            else: p["out"] = now
    redis.set("asia_v60_speed", json.dumps(db))
    return render(), f"Updated: {now}"

with gr.Blocks(css=".gradio-container {background:#000!important;}") as demo:
    gr.HTML("""<div style='text-align:center; border:4px solid #D4AF37; padding:20px; border-radius:20px; background:#111;'>
        <h1 style='color:white!important; margin:0;'>PASTORIA DAILY PRAYER</h1>
        <p style='color:#D4AF37!important; font-weight:bold;'>ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
    </div>""")
    with gr.Row():
        with gr.Column(): out = gr.HTML(render())
        with gr.Column():
            sel = gr.Dropdown([p["n"] for p in pastors_list], label="Priest")
            with gr.Row():
                s_btn = gr.Button("🔥 START", variant="primary")
                f_btn = gr.Button("✅ FINISH")
            msg = gr.Markdown("🟢 Ready")
            with gr.Accordion("🛡️ Admin", open=False):
                pw = gr.Textbox(label="Pass", type="password")
                rs_btn = gr.Button("RESET")

    s_btn.click(act, [sel, gr.State("s")], [out, msg])
    f_btn.click(act, [sel, gr.State("f")], [out, msg])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
