import gradio as gr

# --- ASIA DIVISION SCHEDULE ---
pastors = [
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

def get_status():
    h = "<div style='background:black; padding:20px; border:2px solid #D4AF37; border-radius:10px;'>"
    for p in pastors:
        h += f"<p style='color:white; font-size:1.2em;'>🔥 <b>{p['n']}</b> | <span style='color:#D4AF37;'>{p['s']}</span></p>"
    h += "</div>"
    return h

# --- INTERFACE DESIGN ---
with gr.Blocks(css=".gradio-container {background-color: #000;}") as demo:
    gr.HTML(f"""
        <div style="text-align: center; border-bottom: 2px solid #D4AF37; padding-bottom: 20px; margin-bottom: 20px;">
            <h1 style="color: #D4AF37; font-size: 2.5em; margin-bottom: 0; font-weight: 900;">GOSPEL PILLARS - ASIA DIVISION</h1>
            <p style="color: white; font-style: italic;">Under the Oversight of Apostle Solomon Success</p>
        </div>
    """)
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📜 PROPHETIC STOREHOUSE")
            gr.Button("🎧 Ministry of the Holy Spirit", link="https://macwealthfreestore.com/music/track/prophet_isaiah_macwealth-hosting_the_presence_of_god-the_ministry_of_the_holy_spirit")
            gr.Button("🎧 Grieve Not the Holy Spirit", link="https://macwealthfreestore.com/music/track/dr_isaiah_macwealth-grieve_not_the_holy_spirit-hearing_the_spirit_part_4-grieve_not_the_holy_spirit")
        
        with gr.Column():
            gr.Markdown("### 🔥 LIVE ALTAR WATCH")
            gr.HTML(get_status())

    gr.Button("SIGN IN TO SHIFT (Coming Soon)", variant="primary")

# --- VERCEL EXPORT ---
# We use .mount_gradio_app to make it compatible with Vercel's FastAPI backend
from fastapi import FastAPI
import gradio as gr

app = FastAPI()
app = gr.mount_gradio_app(app, demo, path="/")
