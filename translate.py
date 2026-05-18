import streamlit as st
from openai import OpenAI
import speech_recognition as sr
import pyttsx3

# ====== OpenAI 設定 ======
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# ====== TTS 初始化 ======
tts = pyttsx3.init()

def speak(text):
    tts.say(text)
    tts.runAndWait()

# ====== 翻譯函數 ======
def translate(text, direction):
    if direction == "zh_to_ja":
        system = "請將中文翻譯成自然、禮貌、日本旅遊現場可使用的日文，只輸出一句。"
    else:
        system = "請將日文翻譯成繁體中文，只輸出結果，不要解釋。"

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": text}
        ],
        temperature=0.3
    )

    return res.choices[0].message.content.strip()

# ====== 語音輸入 ======
def voice_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 請說話...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language="zh-TW")
        return text
    except:
        return "無法辨識語音"

# ====== UI ======
st.title("🗼 TokyoTalk MVP（Python版）")

mode = st.radio("翻譯模式", ["中文 → 日文", "日文 → 中文"])

text_input = st.text_input("輸入文字")

col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 語音輸入"):
        text_input = voice_input()
        st.write("辨識結果：", text_input)

with col2:
    if st.button("🔊 朗讀輸入"):
        speak(text_input)

if st.button("🚀 翻譯"):
    if mode == "中文 → 日文":
        result = translate(text_input, "zh_to_ja")
        st.success(result)
        speak(result)
    else:
        result = translate(text_input, "ja_to_zh")
        st.success(result)
        speak(result)