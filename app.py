import streamlit as st
import requests
import copy
import json
import base64

# API Key dan URL
OPENROUTER_API_KEY = "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"
HEADERS = {
  "Authorization": f"Bearer {OPENROUTER_API_KEY}",
  "HTTP-Referer": "https://example-deploy-chatbot.streamlit.app",
  "X-Title": "AI Chatbot Streamlit"
}
API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_OPTIONS = {
    "deepseek/deepseek-chat-v3-0324:free": "Deepseek Chat v3",
    "mistralai/devstral-small:free": "Mistralai Devstral Small",
    "google/gemma-3-27b-it:free": "Google Gemma 3-27b",
    "meta-llama/llama-4-maverick:free": "Meta Llama 4 Maverick"
}

# Layout default
st.set_page_config(layout="wide")

# Session state
if "chat_history_list" not in st.session_state:
    st.session_state.chat_history_list = []
if "current_chat_index" not in st.session_state:
    st.session_state.current_chat_index = -1
if "current_model" not in st.session_state:
    st.session_state.current_model = list(MODEL_OPTIONS.keys())[0]
if "current_chat" not in st.session_state:
    st.session_state.current_chat = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Ambil judul dari pesan user pertama
def chat_title(chat):
    for msg in chat:
        if msg["role"] == "user" and msg["content"].strip():
            return msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")
    return "Chat tanpa judul"

# Sidebar
with st.sidebar:
    st.title("🌟 Menu Chatbot")
    model_name = st.selectbox(
        "Pilih Model Chat", 
        list(MODEL_OPTIONS.values()),
        index=list(MODEL_OPTIONS.keys()).index(st.session_state.current_model)
    )
    for k, v in MODEL_OPTIONS.items():
        if v == model_name:
            st.session_state.current_model = k
            break

    st.markdown("---")
    search_term = st.text_input("Cari chat...", "")
    filtered_indices = [
        i for i, chat in enumerate(st.session_state.chat_history_list)
        if search_term.lower() in chat_title(chat).lower()
    ]
    st.markdown("### Riwayat Chat")
    for i in filtered_indices:
        title = chat_title(st.session_state.chat_history_list[i])
        if st.button(title, key=f"chat_{i}"):
            st.session_state.current_chat_index = i
            st.session_state.current_chat = copy.deepcopy(st.session_state.chat_history_list[i])

    st.markdown("---")
    if st.button("🔄 Reset Chat"):
        st.session_state.current_chat = []
        st.session_state.current_chat_index = -1

# CSS untuk dark mode
if st.session_state.dark_mode:
    dark_css = """
    <style>
    body, .css-18e3th9 { background-color: #121212; color: #eee; }
    .stButton>button { background-color: #333; color: #eee; }
    </style>
    """
    st.markdown(dark_css, unsafe_allow_html=True)

# Judul utama
st.title("AI Chat Bot Buatan Calon Emak Emak 🤖🎉")

# Upload File
uploaded_file = st.file_uploader("📎 Upload file txt/docx/pdf", type=["txt"])
if uploaded_file is not None:
    file_content = uploaded_file.read().decode("utf-8")
    st.text_area("📄 Isi File", file_content, height=150)
    st.session_state.current_chat.append({"role": "user", "content": f"Baca dan ringkas isi file ini:\n{file_content}"})

# Container chat
chat_container = st.container()
with chat_container:
    if st.session_state.current_chat:
        for msg in st.session_state.current_chat:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                st.markdown(f"<div style='text-align:right; background:#3b82f6; color:white; padding:8px; border-radius:10px; margin-bottom:8px;'>{content}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; background:#fff9c4; color:black; padding:8px; border-radius:10px; margin-bottom:8px;'>{content}</div>", unsafe_allow_html=True)

        # Tombol copy ke clipboard
        if st.button("📋 Salin Semua Chat ke Clipboard"):
            full_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.current_chat])
            b64 = base64.b64encode(full_text.encode()).decode()
            js = f"""
            <script>
            const text = atob('{b64}');
            navigator.clipboard.writeText(text).then(function() {{
                alert('Chat telah disalin ke clipboard!');
            }});
            </script>
            """
            st.components.v1.html(js)
    else:
        st.info("Mulai chat dengan mengetik pesan di bawah dan tekan Enter!")

# Chat input
user_input = st.chat_input("Ketik pesanmu di sini...")

if user_input:
    st.session_state.current_chat.append({"role": "user", "content": user_input})

    payload = {
        "model": st.session_state.current_model,
        "messages": [{"role": m["role"], "content": m["content"]} for m in st.session_state.current_chat]
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        response_json = response.json()
        bot_reply = response_json["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        bot_reply = "⏱️ Timeout: Server terlalu lama merespon."
    except requests.exceptions.HTTPError as http_err:
        bot_reply = f"🚨 HTTP Error: {http_err.response.status_code} - {http_err.response.text}"
    except Exception as e:
        bot_reply = f"❌ Error saat menghubungi API: {str(e)}"

    st.session_state.current_chat.append({"role": "assistant", "content": bot_reply})

    if st.session_state.current_chat_index == -1:
        st.session_state.chat_history_list.append(copy.deepcopy(st.session_state.current_chat))
        st.session_state.current_chat_index = len(st.session_state.chat_history_list) - 1
    else:
        st.session_state.chat_history_list[st.session_state.current_chat_index] = copy.deepcopy(st.session_state.current_chat)