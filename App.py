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
    page_title="AI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 2. Complete CSS Fix Engine (DOM-Locked)
# ----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [data-testid="stAppViewContainer"], .main, p, span, div, h1, h2, h3, h4, h5, h6 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        box-sizing: border-box !important;
        word-break: break-word !important;
        overflow-wrap: anywhere !important;
    }

    /* 1. Fluid RGB Charging Background */
    .stApp {
        background: linear-gradient(135deg, #030712 0%, #061126 25%, #081b24 50%, #110926 75%, #030712 100%);
        background-size: 300% 300%;
        animation: chargingAuraFlow 10s ease infinite alternate;
        color: #f8fafc;
    }

    @keyframes chargingAuraFlow {
        0% { background-position: 0% 0%; }
        50% { background-position: 100% 100%; }
        100% { background-position: 0% 100%; }
    }

    /* 2. PERMANENT TOP-LEFT SIDEBAR BUTTON FIX */
    header, [data-testid="stHeader"] {
        background: transparent !important;
    }

    button[kind="header"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] button,
    [data-testid="stHeader"] button {
        background: rgba(10, 16, 35, 0.95) !important;
        border: 1.5px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 8px !important;
        width: 34px !important;
        height: 34px !important;
        min-width: 34px !important;
        min-height: 34px !important;
        color: transparent !important;
        font-size: 0px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.25) !important;
        cursor: pointer !important;
        overflow: hidden !important;
    }

    button[kind="header"] svg,
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="collapsedControl"] svg,
    [data-testid="stHeader"] svg {
        display: none !important;
        visibility: hidden !important;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]::after {
        content: "‹" !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #00f0ff !important;
        line-height: 1 !important;
        display: block !important;
    }

    [data-testid="collapsedControl"] button::after,
    [data-testid="stHeader"] button::after,
    [data-testid="stSidebarCollapseButton"]::after {
        content: "›" !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #00f0ff !important;
        line-height: 1 !important;
        display: block !important;
    }

    /* 3. PROPER CHAT MESSAGE COMPACT BUBBLE STYLING */
    .stChatMessageContainer,
    [data-testid="stChatMessageContainer"] {
        padding: 0 !important;
        margin-bottom: 10px !important;
    }

    [data-testid="stChatMessage"] {
        background: rgba(10, 16, 35, 0.92) !important;
        border: 1.5px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(20px) !important;
        padding: 8px 14px !important;
        width: fit-content !important;
        min-width: 140px !important;
        max-width: 82% !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45) !important;
        transition: all 0.25s ease !important;
    }

    /* User Message: Aligned Right */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        border-left: 3.5px solid #00f0ff !important;
        margin-left: auto !important;
        margin-right: 0 !important;
    }

    /* Assistant Message: Aligned Left */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        border-left: 3.5px solid #00ff87 !important;
        margin-right: auto !important;
        margin-left: 0 !important;
    }

    [data-testid="stChatMessage"]:hover {
        border-color: rgba(0, 240, 255, 0.45) !important;
        box-shadow: 0 6px 22px rgba(0, 240, 255, 0.15) !important;
    }

    /* Code Blocks */
    code, pre, [data-testid="stCodeBlock"] {
        font-family: 'JetBrains Mono', monospace !important;
        background: rgba(3, 7, 18, 0.95) !important;
        border: 1px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 8px !important;
        white-space: pre-wrap !important;
        word-break: break-all !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    /* Live Cursor */
    .laser-typing-cursor {
        display: inline-block;
        width: 3px;
        height: 16px;
        background: #00ff87;
        margin-left: 4px;
        vertical-align: middle;
        animation: blinkCursor 0.7s infinite alternate;
    }

    @keyframes blinkCursor {
        0% { opacity: 0.2; }
        100% { opacity: 1; }
    }

    /* Top Navbar */
    .top-header {
        background: rgba(10, 16, 35, 0.9);
        border: 1.5px solid rgba(0, 240, 255, 0.25);
        border-radius: 16px;
        padding: 10px 18px;
        backdrop-filter: blur(20px);
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }

    .pulse-dot {
        display: inline-block;
        width: 9px;
        height: 9px;
        background: #00ff87;
        border-radius: 50%;
        box-shadow: 0 0 10px #00ff87;
        margin-right: 8px;
    }

    /* Chat Input Bar */
    [data-testid="stChatInput"] {
        background: rgba(10, 16, 35, 0.92) !important;
        border: 1.5px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 20px !important;
        padding: 6px 12px !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.5) !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #00f0ff !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.25) !important;
    }

    [data-testid="stChatInput"] button:first-child {
        background: rgba(0, 240, 255, 0.15) !important;
        border: 1px solid #00f0ff !important;
        color: #00f0ff !important;
        border-radius: 50% !important;
        margin-right: 6px !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, #00f2fe 0%, #00ff87 100%) !important;
        color: #020617 !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
    }

    [data-testid="stSidebar"] {
        background: rgba(6, 10, 24, 0.94) !important;
        border-right: 1px solid rgba(0, 240, 255, 0.2);
        backdrop-filter: blur(25px);
    }

    .clean-auth-card {
        max-width: 380px;
        margin: 40px auto;
        padding: 30px 24px;
        background: rgba(10, 16, 35, 0.9);
        border: 1.5px solid rgba(0, 240, 255, 0.25);
        border-radius: 20px;
        backdrop-filter: blur(20px);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 3. Database Layer (Sessions & 1-Gmail Vault)
# ----------------------------------------------------
DB_FILE = "users_workspace.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            session_title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            is_image INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_user_exists(email: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT email FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    user = c.fetchone()
    conn.close()
    return user is not None

def register_user(email: str, password: str) -> bool:
    clean_email = email.lower().strip()
    if check_user_exists(clean_email):
        return False
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (clean_email, hash_pass(password)))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def authenticate_user(email: str, password: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE LOWER(email) = LOWER(?)", (email.lower().strip(),))
    res = c.fetchone()
    conn.close()
    if res and res[0] == hash_pass(password):
        return True
    return False

def create_new_session(email: str, title: str = "New Chat") -> int:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chat_sessions (user_email, session_title) VALUES (?, ?)", (email.lower().strip(), title))
    sess_id = c.lastrowid
    conn.commit()
    conn.close()
    return sess_id

def get_user_sessions(email: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, session_title FROM chat_sessions WHERE LOWER(user_email) = LOWER(?) ORDER BY id DESC", (email.strip(),))
    rows = c.fetchall()
    conn.close()
    return rows

def rename_session(session_id: int, new_title: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE chat_sessions SET session_title = ? WHERE id = ?", (new_title, session_id))
    conn.commit()
    conn.close()

def delete_session(session_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def save_message_to_db(session_id: int, role: str, content: str, is_image: int = 0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chat_messages (session_id, role, content, is_image) VALUES (?, ?, ?, ?)",
              (session_id, role, content, is_image))
    conn.commit()
    conn.close()

def load_session_messages(session_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content, is_image FROM chat_messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "is_generated_image": bool(r[2])} for r in rows]

# ----------------------------------------------------
# 4. Backend Tunnel Endpoint
# ----------------------------------------------------
OLLAMA_BASE_URL = "https://distributors-individuals-pace-reserves.trycloudflare.com"

# ----------------------------------------------------
# 5. Persistent Authentication Controller
# ----------------------------------------------------
saved_user = st.query_params.get("user", None)

if "authenticated_user" not in st.session_state:
    if saved_user and check_user_exists(saved_user):
        st.session_state.authenticated_user = saved_user
    else:
        st.session_state.authenticated_user = None

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

# ----------------------------------------------------
# 6. Authentication Screen
# ----------------------------------------------------
if not st.session_state.authenticated_user:
    col_l, col_center, col_r = st.columns([1, 1.8, 1])
    with col_center:
        st.markdown("""
        <div class='clean-auth-card'>
            <div class='pulse-dot'></div>
            <h3 style='margin: 8px 0 2px 0; font-weight: 700;'>AI Assistant</h3>
            <p style='color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;'>Sign in to your workspace</p>
        </div>
        """, unsafe_allow_html=True)

        auth_mode = st.radio("Mode", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
        
        email_input = st.text_input("Gmail Address", placeholder="name@gmail.com")
        pass_input = st.text_input("Password", type="password", placeholder="Enter password")

        if auth_mode == "Sign In":
            if st.button("SIGN IN", use_container_width=True):
                clean_email = email_input.lower().strip()
                if not clean_email.endswith("@gmail.com"):
                    st.error("Valid @gmail.com address required.")
                elif not check_user_exists(clean_email):
                    st.error("Account not found. Please create an account first.")
                elif authenticate_user(clean_email, pass_input):
                    st.session_state.authenticated_user = clean_email
                    st.query_params["user"] = clean_email
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        else:
            if st.button("CREATE ACCOUNT", use_container_width=True):
                clean_email = email_input.lower().strip()
                if not clean_email.endswith("@gmail.com"):
                    st.error("Only @gmail.com addresses are permitted.")
                elif len(pass_input) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif check_user_exists(clean_email):
                    st.error("This Gmail is already registered and locked.")
                else:
                    if register_user(clean_email, pass_input):
                        st.success("Account created successfully! Switch to Sign In.")
                    else:
                        st.error("Registration failed. Please try again.")

    st.stop()

# ----------------------------------------------------
# 7. Workspace Setup
# ----------------------------------------------------
user_email = st.session_state.authenticated_user

user_sessions = get_user_sessions(user_email)
if not user_sessions:
    new_id = create_new_session(user_email, "General Chat")
    st.session_state.current_session_id = new_id
    user_sessions = get_user_sessions(user_email)
elif st.session_state.current_session_id is None:
    st.session_state.current_session_id = user_sessions[0][0]

# ----------------------------------------------------
# 8. Sidebar Controls
# ----------------------------------------------------
with st.sidebar:
    st.markdown("### 💬 Chats")
    
    if st.button("➕ New Chat", use_container_width=True):
        new_sess_id = create_new_session(user_email, "New Chat")
        st.session_state.current_session_id = new_sess_id
        st.rerun()

    st.markdown("---")
    
    active_title = "Chat"
    for s_id, s_title in user_sessions:
        if s_id == st.session_state.current_session_id:
            active_title = s_title
            break
            
    with st.expander("✏️ Rename Chat"):
        new_title_input = st.text_input("Title", value=active_title)
        if st.button("Save", use_container_width=True):
            if new_title_input.strip():
                rename_session(st.session_state.current_session_id, new_title_input.strip())
                st.rerun()

    st.markdown("#### Saved Chats")
    
    for s_id, s_title in user_sessions:
        col_select, col_del = st.columns([8, 2])
        with col_select:
            is_active = (s_id == st.session_state.current_session_id)
            label = f"👉 {s_title}" if is_active else s_title
            if st.button(label, key=f"session_{s_id}", use_container_width=True):
                st.session_state.current_session_id = s_id
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"delete_{s_id}"):
                delete_session(s_id)
                st.session_state.current_session_id = None
                st.rerun()

    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated_user = None
        st.session_state.current_session_id = None
        if "user" in st.query_params:
            del st.query_params["user"]
        st.rerun()

# ----------------------------------------------------
# 9. Main Stream
# ----------------------------------------------------
st.markdown(f"""
<div class="top-header">
    <div style="display: flex; align-items: center;">
        <span class="pulse-dot"></span>
        <span style="font-size: 1.1rem; font-weight: 700;">{active_title}</span>
    </div>
    <div style="font-size: 0.8rem; color: #94a3b8;">
        User: <code style="color: #00ff87;">{user_email}</code>
    </div>
</div>
""", unsafe_allow_html=True)

current_messages = load_session_messages(st.session_state.current_session_id)

for msg in current_messages:
    avatar_icon = "🤖" if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        if msg.get("is_generated_image"):
            st.image(msg["content"], caption="Generated Image", use_container_width=True)
        else:
            st.markdown(msg["content"])

# Helpers (Auto-Compression to prevent 524 Timeout)
def encode_img_to_base64(file_obj):
    img = Image.open(file_obj)
    img.thumbnail((640, 640))
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def is_image_request(prompt: str) -> bool:
    triggers = ["photo banao", "image banao", "tasveer banao", "draw", "generate image", "create image", "picture of", "render image"]
    return any(k in prompt.lower() for k in triggers)

# ----------------------------------------------------
# 10. Integrated Chat Input with Native '+' Attachment
# ----------------------------------------------------
user_input = st.chat_input(
    "Ask a question, paste code/math, or attach an image via (+)...",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg"]
)

# ----------------------------------------------------
# 11. Multi-Threaded Execution Pipeline (Zero 524 Timeout)
# ----------------------------------------------------
if user_input:
    user_query = user_input.text if hasattr(user_input, "text") else str(user_input)
    attached_files = getattr(user_input, "files", [])

    if not user_query and not attached_files:
        st.stop()

    if not user_query and attached_files:
        user_query = "Read this image carefully and provide the step-by-step solution."

    if active_title in ["New Chat", "General Chat"] and len(current_messages) == 0:
        short_name = user_query[:24] + "..." if len(user_query) > 24 else user_query
        rename_session(st.session_state.current_session_id, short_name)

    base64_img = None
    if attached_files and len(attached_files) > 0:
        base64_img = encode_img_to_base64(attached_files[0])

    save_message_to_db(st.session_state.current_session_id, "user", user_query, 0)
    with st.chat_message("user", avatar="👤"):
        if attached_files and len(attached_files) > 0:
            st.image(attached_files[0], width=300)
        st.markdown(user_query)

    with st.chat_message("assistant", avatar="🤖"):
        
        # 1. Text-To-Image Generation
        if is_image_request(user_query):
            with st.spinner("Generating image..."):
                encoded_prompt = urllib.parse.quote(user_query)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
                st.image(image_url, caption=f"Prompt: {user_query}", use_container_width=True)
                save_message_to_db(st.session_state.current_session_id, "assistant", image_url, 1)

        # 2. Vision OCR & Step-by-Step Problem Solving (Streaming Anti-524 Engine)
        elif base64_img:
            with st.spinner("Analyzing image and solving..."):
                vision_instruction = (
                    "You are an expert AI assistant. "
                    "1. Read the uploaded image carefully and transcribe all formulas, text, and equations into LaTeX. "
                    "2. Solve the problem step-by-step with clear arithmetic steps. "
                    "3. State the final answer explicitly at the end."
                )
                
                payload = {
                    "model": "minicpm-v",
                    "messages": [
                        {"role": "system", "content": vision_instruction},
                        {
                            "role": "user",
                            "content": f"{user_query}\n\nTranscribe all text from the image, show complete step-by-step working, and compute the final answer.",
                            "images": [base64_img]
                        }
                    ],
                    "options": {
                        "num_thread": 8,
                        "num_ctx": 1024,
                        "temperature": 0.1
                    },
                    "stream": True
                }
                try:
                    response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, stream=True, timeout=120)
                    if response.status_code == 200:
                        placeholder = st.empty()
                        aggregated_text = ""
                        for line in response.iter_lines():
                            if line:
                                data = json.loads(line.decode("utf-8"))
                                chunk = data.get("message", {}).get("content", "")
                                aggregated_text += chunk
                                placeholder.markdown(aggregated_text + "<span class='laser-typing-cursor'></span>", unsafe_allow_html=True)
                        placeholder.markdown(aggregated_text)
                        save_message_to_db(st.session_state.current_session_id, "assistant", aggregated_text, 0)
                    else:
                        st.error(f"Vision Server Alert: Status {response.status_code}")
                except Exception as ex:
                    st.error(f"Connection failure: {str(ex)}")

        # 3. Step-by-Step Deep Reasoning Engine (DeepSeek-R1 8B with 8 Threads)
        else:
            system_prompt = {
                "role": "system",
                "content": (
                    "You are an expert, direct, and intelligent AI assistant. "
                    "Provide clear, accurate, and step-by-step solutions for mathematics, science, programming, and general questions. "
                    "Use LaTeX for formulas and state the final result clearly."
                )
            }

            clean_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in current_messages[-4:]
                if not m.get("is_generated_image")
            ]

            payload = {
                "model": "deepseek-r1:8b",
                "messages": [system_prompt] + clean_messages + [{"role": "user", "content": user_query}],
                "keep_alive": "24h",
                "options": {
                    "num_thread": 8,
                    "num_ctx": 4096,
                    "temperature": 0.1
                },
                "stream": True
            }

            try:
                response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, stream=True, timeout=120)
                if response.status_code == 200:
                    placeholder = st.empty()
                    aggregated_text = ""
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            chunk = data.get("message", {}).get("content", "")
                            aggregated_text += chunk
                            placeholder.markdown(aggregated_text + "<span class='laser-typing-cursor'></span>", unsafe_allow_html=True)
                    placeholder.markdown(aggregated_text)
                    save_message_to_db(st.session_state.current_session_id, "assistant", aggregated_text, 0)
                else:
                    st.error(f"Server Alert: Status {response.status_code}")
            except Exception as ex:
                st.error(f"Stream error: {str(ex)}")
