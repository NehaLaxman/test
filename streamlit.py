import streamlit as st
import requests
st.title("BFL Chatbot")

user_input = st.text_input("You: ", "")

if st.button("Send"):
    chat_url = "http://localhost:8000/chat"
    response = requests.post(chat_url, json={"message": user_input,"session_id": None}).json()
    st.text_area("Bot: ", value=response["reply"], height=300)
