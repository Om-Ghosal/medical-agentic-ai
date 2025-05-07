import streamlit as st
from aws_polly_translate import polly_pipieline,aws_transcribe_stream,aws_translation

import requests

import base64

st.set_page_config(
    page_title="Medical Agentic AI",  # Can be an emoji or a URL/path to an image
)
if "messages" not in st.session_state:
    st.session_state["messages"]=[{"role":"ai","content":"Hello !, How can i help you today ? 😊"}]


def autoplay_audio(audio_data):
    # Encode audio data to base64
    b64_audio = base64.b64encode(audio_data).decode()
    audio_html = f"""
        <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
        </audio>
        """
    st.markdown(audio_html, unsafe_allow_html=True)

def save_audio(audio_data):
    filename='temp.mp3'
    with open(filename, "wb") as f:
        f.write(audio_data.getbuffer()) 

def transaction_dict(d):
    if not isinstance(d, dict):
        return False
    return all(isinstance(k, str) and isinstance(v, int) for k, v in d.items())
def query_ai(query):
    url = 'http://localhost:8000/query'
    response = requests.post(url,json={'q':query}).json()

    return response

def query_form_ai(query, image_file_name):
    url = 'http://localhost:8000/formquery'
    with open(image_file_name, "rb") as img_file:
        files = {"form": (image_file_name, img_file, "image/png")}
        data = {'q': query}
        response = requests.post(url, files=files, data=data).json()
    return response

def save_img_locally(uploaded_file):
    file_path = uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
languages = {
    'English': 'en-IN',   # American English (others include en-GB, en-AU, etc.)
    'Hindi': 'hi-IN',
    'Chinese': 'zh-CN'   # Mandarin Chinese (Simplified, China)
}

voice_id = {
    'English':'Kajal',
    'Hindi':'Kajal',
    'Chinese':'Zhiyu'
}
translate_language_codes = {
    'English': 'en',
    'Hindi': 'hi',
    'Chinese': 'zh'  # Simplified Chinese
}


st.title("Medical Agentic AI")

with st.sidebar:


    st.subheader("Voice",divider='orange')
    audio_query=st.audio_input("Ask a Query ?",help="Ask the AI agent directly using your Voice")
    voice_enabled = st.checkbox("Voice Enabled",value=False)
    voice = st.selectbox("Language",(languages.keys()),help='Select the language in which you want to interact with the AI agent')

    
    # Pass the query through audio
    if audio_query:
        save_audio(audio_query)
        text=aws_transcribe_stream(languages[voice])
        st.session_state['messages'].append({"role":"user","content":f"{text}"})

        if voice!='English':
            text = aws_translation(text,source_language=translate_language_codes[voice])
            
        response = query_ai(text)

        if voice!='English':
            translated_text=aws_translation(response,target_language=translate_language_codes[voice])
    
            st.session_state['messages'].append({"role":"ai","content":translated_text})
        else:
            st.session_state['messages'].append({"role":"ai","content":response})

        if voice_enabled:
            audio_data = polly_pipieline(response,to_language=languages[voice],lang_id=languages[voice],voice_id=voice_id[voice])
            autoplay_audio(audio_data)

# Show the Messages
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        if transaction_dict(message['content']):
            st.line_chart(message['content'],x_label='Year',y_label='Expendature')
        else:
            st.markdown(message['content'])


# Pass the query through typing
if prompt:=st.chat_input("Enter your query 🔍",accept_file=True,file_type=['jpg','png','pdf']):

    with st.chat_message("user"):
        st.markdown(prompt.text)

    st.session_state["messages"].append({"role":"user","content":prompt.text})
    if voice!='English':
        prompt = aws_translation(prompt.text,source_language=translate_language_codes[voice])
    

    with st.chat_message("ai"):
        message_placeholder = st.empty()

        if not prompt.files:
            response = query_ai(prompt.text)
        else:
            print(prompt.files)
            save_img_locally(prompt.files[0])
            response = query_form_ai(prompt.text,prompt.files[0].name)

        if voice!='English':
            translated_text=aws_translation(response,target_language=translate_language_codes[voice])
            st.markdown(translated_text)

        else:
            st.markdown(response)

        if voice_enabled:
    
            audio_data = polly_pipieline(response,to_language=translate_language_codes[voice],lang_id=languages[voice],voice_id=voice_id[voice])
            autoplay_audio(audio_data)
            
    if voice!='English':
        st.session_state["messages"].append({"role":"ai","content":translated_text})  
    else:
        st.session_state["messages"].append({"role":"ai","content":response})  
    