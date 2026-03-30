import gradio as gr
from datetime import datetime, timedelta
import json
import os
from fastapi import FastAPI
from upstash_redis import Redis

# --- FAST DATABASE LINK ---
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

def calculate_duration(start_str, end_str):
    if start_str == "--" or end_str == "--": return ""
    fmt = "%I:%M %p"
    try:
        t1 = datetime.strptime(start_str, fmt)
        t2 = datetime.strptime(end_str, fmt)
        if t2 <= t1: t2 += timedelta(days=1)
        diff = t2 - t1
        mins = int(diff.total_seconds() / 60)
        return f"{mins//60}h {mins%60}m"
    except: return ""

def load_db():
    try:
        raw = redis.get("asia_final_v100")
        if raw: return json.loads(raw)
    except: pass
    return [{"n": p["n"], "s": p["s"], "st": "Waiting", "in": "--", "out": "--", "dur": ""} for p in pastors_list]

def get_stats(data):
    total_pastors = sum(1 for p in data if p["in"] != "--")
    return f"### 📊 TOTAL PASTORS SIGNED IN: {total_pastors}"

def render():
    data = load_db()
    html = f"<div style='background:#000; padding:10px;'>"
    for p in data:
        is_p = "Praying" in p["st"]
        bg = "#D4AF37" if is_p else "#FFF"
        html += f"""<div style="background:{bg}; border:3px solid #D4AF37; padding:12px; margin-bottom:8px; border-radius:12px; color:#000;">
            <div style="display:flex; justify-content:space-between;">
                <b>{p['n']}</b> <b>{'🔥 ' if is_p else ''}{p['st']}</b>
            </div>
            <div style="font-size:0.85em; font-weight: bold;">
                {p['s']} | {p['in']} - {p['out']} <span style="color:red;">{f'({p["dur"]})' if p["dur"] else ''}</span>
            </div>
        </div>"""
    return html + "</div>", get_stats(data)

def act(name, m):
    if not name: return render()[0], "⚠️ Select Name", render()[1]
    db = load_db()
    now = (datetime.utcnow() + timedelta(hours=1)).strftime("%I:%M %p")
    for p in db:
        if p["n"] == name:
            if m == "s":
                p.update({"st": "Praying", "in": now, "out": "--", "dur": ""})
            else:
                p["st"], p["out"] = "✅ Done", now
                p["dur"] = calculate_duration(p["in"], now)
    redis.set("asia_final_v100", json.dumps(db))
    return render()[0], f"Recorded: {now}", get_stats(db)

def reset(pwd):
    if pwd != ADMIN_PASSWORD: return render()[0], "❌ Denied", render()[1]
    db = [{"n": p["n"], "s": p["s"], "st": "Waiting", "in": "--", "out": "--", "dur": ""} for p in pastors_list]
    redis.set("asia_final_v100", json.dumps(db))
    return render()[0], "🔄 Altar Cleared", get_stats(db)

with gr.Blocks(css=".gradio-container {background:#000!important;} * {color: #D4AF37!important;}") as demo:
    # THE TITLE (Exactly as requested)
    gr.HTML("""<div style='text-align:center; border:4px solid #D4AF37; padding:20px; border-radius:20px; background:#111;'>
        <h1 style='color:white!important; margin:0;'>PASTORIA DAILY PRAYER</h1>
        <p style='color:white!important; margin:5px;'>GOSPEL PILLARS MINISTRY INTERNATIONAL</p>
        <hr style='border:0; border-top:1px solid #D4AF37; width:60%; margin:10px auto;'>
        <p style='color:#D4AF37!important; font-weight:bold; text-transform:uppercase;'>ASIA DIVISION HEAD | APOSTLE SOLOMON SUCCESS</p>
    </div>""")
    
    with gr.Row():
        with gr.Column():
            list_out = gr.HTML(render()[0])
            stats_out = gr.Markdown(render()[1])
        with gr.Column():
            sel = gr.Dropdown([p["n"] for p in pastors_list], label="Priest Name")
            with gr.Row():
                s_btn = gr.Button("🔥 START", variant="primary")
                f_btn = gr.Button("✅ FINISH")
            msg = gr.Markdown("🟢 System Ready")
            with gr.Accordion("🛡️ Admin Panel", open=False):
                pw = gr.Textbox(label="Pass", type="password")
                rs = gr.Button("RESET FOR NEW DAY")

    s_btn.click(act, [sel, gr.State("s")], [list_out, msg, stats_out])
    f_btn.click(act, [sel, gr.State("f")], [list_out, msg, stats_out])
    rs.click(reset, [pw], [list_out, msg, stats_out])

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
