import streamlit as st
import ollama
import json
import speech_recognition as sr
import io
from PyPDF2 import PdfReader
from docx import Document

st.set_page_config(page_title="本地智慧對話系統", layout="wide")

# --- 初始化狀態 ---
if "conversations" not in st.session_state:
    st.session_state.conversations = {}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = "新對話"

# --- 側邊欄：對話管理 ---
st.sidebar.title("🗂️ 對話列表")
chat_titles = list(st.session_state.conversations.keys())
selected = st.sidebar.radio("選擇對話", ["新對話"] + chat_titles)

if selected != st.session_state.active_chat:
    st.session_state.active_chat = selected

if st.session_state.active_chat not in st.session_state.conversations:
    st.session_state.conversations[st.session_state.active_chat] = []

chat_history = st.session_state.conversations[st.session_state.active_chat]
st.title(f"💬 {st.session_state.active_chat}")

# --- 聊天記錄顯示 ---
for msg in chat_history:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.markdown(msg["content"])

# --- 語音輸入區塊 ---
with st.sidebar.expander("🎙️ 語音輸入"):
    if st.button("🎤 開始語音輸入"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("請開始說話...")
            audio = recognizer.listen(source, timeout=5)
            try:
                text = recognizer.recognize_google(audio, language="zh-TW")
                st.success(f"辨識結果：{text}")
                st.session_state.voice_input = text
            except Exception as e:
                st.error(f"語音辨識失敗：{e}")
    voice_input = st.session_state.get("voice_input", "")

# --- 檔案上傳 RAG ---
with st.sidebar.expander("📎 上傳文件提問 (txt/pdf/docx)"):
    uploaded_file = st.file_uploader("上傳文件", type=["txt", "pdf", "docx"])
    file_text = ""
    if uploaded_file:
        ext = uploaded_file.name.split(".")[-1]
        if ext == "txt":
            file_text = uploaded_file.read().decode("utf-8")
        elif ext == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                file_text += page.extract_text()
        elif ext == "docx":
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                file_text += para.text + "\n"
        st.success("檔案上傳成功，可提問內容。")

        rag_question = st.text_input("📄 請輸入關於檔案的問題")
        if st.button("📡 問檔案內容"):
            file_messages = [
                {"role": "system", "content": "你是一個可以根據文件回答問題的助手"},
                {"role": "user", "content": f"文件內容如下：\n{file_text}"},
                {"role": "user", "content": rag_question}
            ]
            response = ollama.chat(model="mistral", messages=file_messages)
            st.info("回答：")
            st.write(response["message"]["content"])

# --- 使用者輸入 ---
user_input = st.chat_input("請輸入訊息...") or voice_input
if user_input:
    chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = ollama.chat(model="mistral", messages=chat_history)
            reply = response["message"]["content"]
            st.markdown(reply)
            chat_history.append({"role": "assistant", "content": reply})

# --- 建立新對話 ---
with st.sidebar.expander("➕ 建立新對話"):
    new_name = st.text_input("輸入新對話名稱")
    if st.button("建立") and new_name.strip():
        if new_name in st.session_state.conversations:
            st.warning("此對話名稱已存在！請換一個")
        else:
            st.session_state.conversations[new_name] = []
            st.session_state.active_chat = new_name
            st.rerun()

# --- 刪除目前對話 ---
with st.sidebar.expander("🗑️ 刪除目前對話"):
    if st.session_state.active_chat != "新對話":
        if st.button("刪除此對話"):
            del st.session_state.conversations[st.session_state.active_chat]
            st.session_state.active_chat = "新對話"
            st.rerun()
    else:
        st.info("請先選擇一個要刪除的對話")

# --- 匯出對話紀錄 ---
with st.sidebar.expander("📤 匯出所有對話紀錄"):
    if st.button("下載 JSON"):
        exported_data = json.dumps(st.session_state.conversations, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 下載 conversations.json",
            data=exported_data,
            file_name="conversations.json",
            mime="application/json"
        )

# --- 匯入對話紀錄 ---
with st.sidebar.expander("📥 匯入對話紀錄"):
    uploaded_json = st.file_uploader("上傳 JSON 檔", type="json", key="import_json")
    if uploaded_json is not None:
        try:
            imported_data = json.load(uploaded_json)
            if isinstance(imported_data, dict):
                st.session_state.conversations.update(imported_data)
                st.success("✅ 對話紀錄匯入成功！")
                st.rerun()
            else:
                st.error("⚠️ 檔案格式錯誤，請確認是對話 JSON 結構。")
        except Exception as e:
            st.error(f"⚠️ 匯入失敗：{e}")
