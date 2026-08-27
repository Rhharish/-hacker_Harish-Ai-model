import streamlit as st
import sqlite3
import hashlib
import requests
import json
import base64
import urllib.parse
from io import BytesIO
from PIL import Image

# ----------------------------------------------------
# 1. Page Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="AI Workspace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------
# 2. Clean Animated Dark UI
# ----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #020617 100%);
        color: #f8fafc;
    }

    /* Auth Card Animation */
    .auth-card {
        max-width: 400px;
        margin: 60px auto;
        padding: 35px 30px;
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        backdrop-filter: blur(16px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        animation: fadeIn 0.5s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Chat Messages */
    [data-testid="stChatMessage"] {
        background: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px);
        margin-bottom: 12px;
        animation: slideUp 0.3s ease-out;
    }

    @keyframes slideUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Custom File Upload Box */
    .stFileUploader {
        margin-bottom: 10px;
    }

    /* Primary Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #38bdf8 0%, #2563eb 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 3. Database Management (Auth & User History)
# ----------------------------------------------------
DB_FILE = "users_workspace.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            role TEXT,
            content TEXT,
            is_image INTEGER DEFAULT 0,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (email.lower().strip(), hash_pass(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE email = ?", (email.lower().strip(),))
    res = c.fetchone()
    conn.close()
    if res and res[0] == hash_pass(password):
        return True
    return False

def save_chat_to_db(email, role, content, is_image=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (user_email, role, content, is_image) VALUES (?, ?, ?, ?)",
              (email, role, content, is_image))
    conn.commit()
    conn.close()

def load_user_chats(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content, is_image FROM chat_history WHERE user_email = ? ORDER BY id ASC", (email,))
    rows = c.fetchall()
    conn.close()
    chats = []
    for r in rows:
        chats.append({
            "role": r[0],
            "content": r[1],
            "is_generated_image": bool(r[2])
        })
    return chats

def clear_user_chats(email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE user_email = ?", (email,))
    conn.commit()
    conn.close()

# ----------------------------------------------------
# 4. Backend Tunnel Endpoint
# ----------------------------------------------------
OLLAMA_BASE_URL = "https://joseph-dependent-hardcover-gerald.trycloudflare.com"

# ----------------------------------------------------
# 5. Session State Control
# ----------------------------------------------------
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------------------------------
# 6. Authentication Screen
# ----------------------------------------------------
if not st.session_state.authenticated_user:
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>Sign In</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.9rem; margin-bottom: 25px;'>Access your workspace</p>", unsafe_allow_html=True)

    auth_mode = st.radio("Choose Mode", ["Login", "Create Account"], horizontal=True, label_visibility="collapsed")
    
    email_input = st.text_input("Gmail Address", placeholder="name@gmail.com")
    pass_input = st.text_input("Password", type="password", placeholder="Enter your password")

    if auth_mode == "Login":
        if st.button("Sign In", use_container_width=True):
            if not email_input.endswith("@gmail.com"):
                st.error("Please enter a valid @gmail.com address.")
            elif authenticate_user(email_input, pass_input):
                st.session_state.authenticated_user = email_input.lower().strip()
                st.session_state.messages = load_user_chats(st.session_state.authenticated_user)
                st.rerun()
            else:
                st.error("Invalid Gmail or password.")
    else:
        if st.button("Create Account", use_container_width=True):
            if not email_input.endswith("@gmail.com"):
                st.error("Only @gmail.com addresses are allowed.")
            elif len(pass_input) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                if register_user(email_input, pass_input):
                    st.success("Account created successfully! You can now log in.")
                else:
                    st.error("An account with this Gmail already exists.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ----------------------------------------------------
# 7. Authenticated Workspace
# ----------------------------------------------------
user_email = st.session_state.authenticated_user

# Top Navigation Bar
top_col1, top_col2, top_col3 = st.columns([6, 2, 2])
with top_col1:
    st.markdown(f"### ✨ AI Workspace")
    st.caption(f"Account: `{user_email}`")
with top_col2:
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
with top_col3:
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated_user = None
        st.session_state.messages = []
        st.rerun()

# Sidebar Settings
with st.sidebar:
    st.markdown("### Workspace Settings")
    mode_option = st.selectbox(
        "Response Mode",
        ["Deep Thinking (High Accuracy)", "Fast Response (Speed Optimized)"],
        index=0
    )
    st.markdown("---")
    if st.button("Delete Chat History", use_container_width=True):
        clear_user_chats(user_email)
        st.session_state.messages = []
        st.rerun()

# Internal Model Routing (Hidden from User)
selected_model_engine = "deepseek-r1:1.5b" if "Deep" in mode_option else "qwen2.5:1.5b"

# Render Existing Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image_display"):
            st.image(msg["image_display"], caption="Attached Context", width=320)
        if msg.get("is_generated_image"):
            st.image(msg["content"], caption="Generated Image", use_container_width=True)
        else:
            st.markdown(msg["content"])

# Multi-Modal Upload Container
uploaded_file = st.file_uploader("📎 Upload Image or Document for analysis", type=["png", "jpg", "jpeg"])
user_query = st.chat_input("Ask any question, solve math/code, or describe an image to create...")

# Helper Functions
def encode_img_to_base64(file_obj):
    img = Image.open(file_obj)
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def is_image_request(prompt: str) -> bool:
    triggers = ["photo banao", "image banao", "tasveer banao", "draw", "generate image", "create image", "picture of", "render"]
    return any(k in prompt.lower() for k in triggers)

# ----------------------------------------------------
# 8. Request Processing & Inference Engine
# ----------------------------------------------------
if user_query:
    user_entry = {"role": "user", "content": user_query}
    base64_img = None

    if uploaded_file is not None:
        base64_img = encode_img_to_base64(uploaded_file)
        user_entry["image_display"] = uploaded_file

    st.session_state.messages.append(user_entry)
    save_chat_to_db(user_email, "user", user_query, 0)

    with st.chat_message("user"):
        if uploaded_file is not None:
            st.image(uploaded_file, width=320)
        st.markdown(user_query)

    with st.chat_message("assistant"):
        
        # ROUTE 1: Text-To-Image Generation
        if is_image_request(user_query):
            with st.spinner("Creating image..."):
                encoded_prompt = urllib.parse.quote(user_query)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                st.image(image_url, caption="Generated Image", use_container_width=True)
                
                st.session_state.messages.append({"role": "assistant", "content": image_url, "is_generated_image": True})
                save_chat_to_db(user_email, "assistant", image_url, 1)

        # ROUTE 2: Vision & Multimodal Image Analysis
        elif base64_img:
            with st.spinner("Analyzing image..."):
                payload = {
                    "model": "moondream",
                    "messages": [{
                        "role": "user",
                        "content": user_query if user_query else "Analyze this image and explain everything in detail.",
                        "images": [base64_img]
                    }],
                    "stream": False
                }
                try:
                    res = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
                    if res.status_code == 200:
                        out = res.json().get("message", {}).get("content", "No response.")
                        st.markdown(out)
                        st.session_state.messages.append({"role": "assistant", "content": out})
                        save_chat_to_db(user_email, "assistant", out, 0)
                    else:
                        st.error(f"Image analysis error: Status {res.status_code}")
                except Exception as ex:
                    st.error(f"Connection failed: {str(ex)}")

        # ROUTE 3: Universal Knowledge, STEM, Math, Coding Stream
        else:
            universal_system_prompt = {
                "role": "system",
                "content": "You are an all-knowing, highly capable universal AI assistant. You excel in answering any general knowledge questions from around the world, as well as complex mathematical calculations, scientific theories, advanced computer programming, and creative writing. Provide accurate, clear, and comprehensive answers."
            }

            clean_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[-4:]
                if not m.get("is_generated_image") and not m.get("image_display")
            ]

            payload = {
                "model": selected_model_engine,
                "messages": [universal_system_prompt] + clean_messages,
                "keep_alive": "24h",
                "options": {
                    "num_thread": 4,
                    "num_ctx": 1024,
                    "temperature": 0.6
                },
                "stream": True
            }

            try:
                response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, stream=True, timeout=90)
                if response.status_code == 200:
                    placeholder = st.empty()
                    aggregated_text = ""
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            chunk = data.get("message", {}).get("content", "")
                            aggregated_text += chunk
                            placeholder.markdown(aggregated_text + "▌")
                    placeholder.markdown(aggregated_text)
                    st.session_state.messages.append({"role": "assistant", "content": aggregated_text})
                    save_chat_to_db(user_email, "assistant", aggregated_text, 0)
                else:
                    st.error(f"Server Error: Status code {response.status_code}")
            except Exception as ex:
                st.error(f"Network error: {str(ex)}")