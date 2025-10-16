import streamlit as st
from streamlit import spinner
from streamlit.web.server.server import server_port_is_manually_set
from you_tube import (
     extract_video_id,
     get_transcript,
     translate_transcript,
     generate_notes,
     get_important_topics,
     create_chunks,
     create_vector_store,
     rag_answer
)
from chatbot_backend import chatbot
from langchain_core.messages import HumanMessage


# --sidebar--
with st.sidebar:
    st.title('AI Chatbot')
    st.markdown('----')
    st.markdown('Ask the AI')
    chat_button=st.button('Chat with AI')
    st.markdown('----')
    st.title("YT Agent")
    st.markdown("### Input Details")

    youtube_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    language = st.text_input("Video Language Code", placeholder="e.g., en, hi, es, fr", value="en")

    task_option=st.radio(
        'choose what you want to generate:',
        ['chat with video','notes for you']
    )

    submit_button=st.button('Start Processing')
    st.markdown('----')

    # --- Main Page ---
st.title("Studentpedia")
st.markdown("Ask question and interact with the AI.")

#--processing Flow--
if chat_button:
    st.session_state.pop("vector_store", None)
    st.session_state["message_history"] = []
    st.session_state.is_chat_active = True # activate chat mode

if st.session_state.get("is_chat_active", False):
    CONFIG = {'configurable': {'thread_id': 'thread-1'}}

    if 'message_history' not in st.session_state:
        st.session_state['message_history'] = []

    # loading the conversation history
    for message in st.session_state['message_history']:
        with st.chat_message(message['role']):
            st.text(message['content'])

    #{'role': 'user', 'content': 'Hi'}
    #{'role': 'assistant', 'content': 'Hi=ello'}

    user_input = st.chat_input('Type here')

    if user_input:

        # first add the message to message_history
        st.session_state['message_history'].append({'role': 'user', 'content': user_input})
        with st.chat_message('user'):
            st.text(user_input)

        with st.chat_message('assistant'):

            ai_message = st.write_stream(
                message_chunk.content for message_chunk, metadata in chatbot.stream(
                    {'messages': [HumanMessage(content=user_input)]},
                    config= {'configurable': {'thread_id': 'thread-1'}},
                    stream_mode= 'messages'
                )
            )

        st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

if submit_button:
    if youtube_url and language:
        video_id=extract_video_id(youtube_url)
        if video_id:
            with spinner('step 1/3:Fetching Transcript....'):
                full_transcript=get_transcript(video_id,language)

                if language!='en':
                    with spinner('step 1.5/3: Translating Transcript into english, this may take few seconds...'):
                        full_transcript=translate_transcript(full_transcript)   

            if task_option=='notes for you':
                with spinner('step 2/3: Extracting important topics...'):
                    important_topics=get_important_topics(full_transcript)
                    st.subheader('important topics')
                    st.write(important_topics)
                    st.markdown('----')
                
                with spinner('step 3/3 : generating notes for you'):
                    notes=generate_notes(full_transcript)
                    st.subheader("Notes for you")
                    st.write(notes)
                st.success('Summary and Notes Generated.')
            
            if task_option=='chat with video':
                st.session_state.pop("message_history", None)
                with st.spinner('step 2/3: creating chunks and vectore store....'):
                    chunks = create_chunks(full_transcript)
                    vectorstore = create_vector_store(chunks)
                    st.session_state.vector_store = vectorstore
                st.session_state.messages=[]
                st.success('Video is ready for chat.....')

# chatbot session
if task_option=="chat with video" and "vector_store" in st.session_state:
    st.session_state.pop("message_history", None)
    st.divider()
    st.subheader("Chat with Video")

    # Display the entire history
    for message in st.session_state.get('messages',[]):
        st.session_state.pop("message_history", None)
        with st.chat_message(message['role']):
            st.write(message['content'])

    # user_input
    prompt= st.chat_input("Ask me anything about the video.")
    if prompt:
        st.session_state.messages.append({'role':'user','content':prompt})
        with st.chat_message('user'):
            st.write(prompt)

        with st.chat_message('assistant'):
           response= rag_answer(prompt,st.session_state.vector_store)
           st.write(response)
        st.session_state.messages.append({'role': 'assistant', 'content':response})
