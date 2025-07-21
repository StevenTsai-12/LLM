import streamlit as st
import ollama

# 頁面設定
st.set_page_config(page_title="自然語言對話程式", layout="wide")

# 初始化狀態
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = "新對話"

# 側邊欄：對話管理
st.sidebar.title("🗂️ 歷史對話")
chat_titles = list(st.session_state.conversations.keys())
selected = st.sidebar.radio("選擇對話", ["新對話"] + chat_titles)

# 切換對話
if selected != st.session_state.active_chat:
    st.session_state.active_chat = selected

# 新對話初始化
if st.session_state.active_chat not in st.session_state.conversations:
    st.session_state.conversations[st.session_state.active_chat] = []

# 主區域
st.title(f"💬 {st.session_state.active_chat}")
chat_history = st.session_state.conversations[st.session_state.active_chat]

# 顯示歷史訊息
for msg in chat_history:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# 輸入框 + 送出按鈕
user_input = st.chat_input("請輸入訊息...")
if user_input:
    # 加入使用者輸入
    chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 呼叫 Ollama 回覆
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = ollama.chat(model="mistral", messages=chat_history)
            reply = response["message"]["content"]
            st.markdown(reply)
            chat_history.append({"role": "assistant", "content": reply})

# 新對話按鈕
if st.sidebar.button("➕ 建立新對話"):
    new_name = f"對話 {len(chat_titles) + 1}"
    st.session_state.conversations[new_name] = []
    st.session_state.active_chat = new_name
    st.rerun()
