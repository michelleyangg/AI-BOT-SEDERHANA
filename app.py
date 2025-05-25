import streamlit as st
import requests
import base64
from textblob import TextBlob
import json
import copy

# API Key dan URL
OPENROUTER_API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

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

# Fungsi copy
def copy_to_clipboard(text):
    js_code = f"""
    <script>
    navigator.clipboard.writeText(`{text}`);
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

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
    st.session_state.dark_mode = st.checkbox("🌃 Dark Mode", value=st.session_state.dark_mode)

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
    uploaded_file = st.file_uploader("Upload gambar untuk dikirim ke chat", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        img_bytes = uploaded_file.read()
        img_b64 = base64.b64encode(img_bytes).decode()
        img_markdown = f"![uploaded_image](data:image/png;base64,{img_b64})"
        st.session_state.current_chat.append({"role": "user", "content": img_markdown})

        if st.session_state.current_chat_index == -1:
            st.session_state.chat_history_list.append(copy.deepcopy(st.session_state.current_chat))
            st.session_state.current_chat_index = len(st.session_state.chat_history_list) - 1
        else:
            st.session_state.chat_history_list[st.session_state.current_chat_index] = copy.deepcopy(st.session_state.current_chat)

    st.markdown("---")
    if st.button("📋 Share Chat (copy ke clipboard)"):
        if st.session_state.current_chat:
            full_chat_text = "\n\n".join(
                [f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.current_chat]
            )
            copy_to_clipboard(full_chat_text)
            st.success("Chat berhasil disalin ke clipboard!")
        else:
            st.warning("Tidak ada chat untuk disalin.")

    st.markdown("---")
    if st.button("🔄 Reset Chat"):
        st.session_state.current_chat = []
        st.session_state.current_chat_index = -1

    st.markdown("---")
    if st.session_state.current_chat:
        chat_json = json.dumps(st.session_state.current_chat, indent=2)
        b64 = base64.b64encode(chat_json.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="chat_history.json">⬇️ Download Chat History (.json)</a>'
        st.markdown(href, unsafe_allow_html=True)

# CSS untuk dark mode saja
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
    else:
        st.info("Mulai chat dengan mengetik pesan di bawah dan tekan Enter!")

# Input pesan
user_input = st.text_input("Ketik pesanmu di sini dan tekan Enter:", value="", placeholder="Tulis pesanmu di sini...")

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
