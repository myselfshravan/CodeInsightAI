import os
import time

import streamlit as st
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from interface import OpenAIChatAgent
from api import RespondAPI

st.set_page_config(page_title='Ask the Code App', page_icon='🧑‍💻')

selected_model = "codellama/CodeLlama-70b-Instruct-hf"
if "api" not in st.session_state: st.session_state.api = RespondAPI(st.secrets, respond_col="respond")
api = st.session_state.api
if "agent" not in st.session_state:
    st.session_state.agent = OpenAIChatAgent(selected_model)
    st.session_state.agent.OPENAI_API_KEY = st.secrets.OPENAI_API_KEY
    st.session_state.agent.ANYSCALE_API_KEY = st.secrets.ANYSCALE_API_KEY
if "respond_id" not in st.session_state: st.session_state.respond_id = None
if "code_input" not in st.session_state: st.session_state.code_input = ""
if "query_text" not in st.session_state: st.session_state.query_text = ""
if 'result' not in st.session_state: st.session_state.result = ""


def reset_session():
    st.session_state.clear()
    st.session_state.api = api


def load_respond(respond):
    st.session_state.respond_id = respond.id
    st.session_state.code_input = respond.get("code_input")
    st.session_state.result = respond.get("respond_text")
    st.session_state.query_text = respond.get("query_text")


def delete_respond(respond):
    if respond.id == st.session_state.respond_id: reset_session()
    respond.reference.delete()


def message_stream(text: str):
    for ch in text:
        yield ch
        time.sleep(0.005)


with st.sidebar:
    st.markdown(f"<h1 style='color:white;'> Welcome!</h1>", unsafe_allow_html=True)
    st.divider()
    c1, _ = st.columns([4, 1])
    c1.button(
        "New Respond",
        on_click=reset_session,
        type="primary" if st.session_state.respond_id is None else "secondary",
        use_container_width=True,
    )

    responds = list(api.get_responds())
    sorted_responds = sorted(responds, key=lambda x: x.get("timestamp"), reverse=True)

    for _respond in sorted_responds:
        c1, c2 = st.columns([4, 1])
        c1.button(
            _respond.id,
            on_click=lambda respond=_respond: load_respond(respond),
            type="primary" if _respond.id == st.session_state.respond_id else "secondary",
            use_container_width=True,
        )
        c2.button("🗑", on_click=lambda respond=_respond: delete_respond(respond), use_container_width=True,
                  key=_respond.id)


def generate_response(uploaded_file, openai_api_key, query_text):
    # Load document if file is uploaded
    if uploaded_file is not None:
        documents = [uploaded_file.read().decode()]
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.create_documents(documents)
        # Select embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        # Create a vectorstore from documents
        db = Chroma.from_documents(texts, embeddings)
        # Create retriever interface
        retriever = db.as_retriever()
        # Create QA chain
        qa = RetrievalQA.from_chain_type(llm=OpenAI(openai_api_key=openai_api_key), chain_type='stuff',
                                         retriever=retriever)
        return qa.run(query_text)


st.title('Ask the Code App')
st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)

if st.session_state.result:
    with st.expander('Code', expanded=True):
        st.code(st.session_state.code_input)
    st.caption('The above code was used to generate the response.')
    st.divider()
    st.write('User Query:')
    st.info(st.session_state.query_text)
    st.write('AI Response:')
    st.write(st.session_state.result)

else:
    input_type = st.radio('Choose the input method:', ['Type', 'Upload'], index=0, horizontal=True, key='input_method')
    uploaded_file = None
    input_text = ''
    if input_type == 'Upload':
        uploaded_file = st.file_uploader('Upload the code', type=['py', 'js', 'jsx'], accept_multiple_files=True,
                                         key='file_uploader')
    elif input_type == 'Type':
        input_text = st.text_area('Enter your code here:', placeholder='Please the code.', height=300,
                                  value=st.session_state.code_input)

    query_text = st.text_input('Enter your question:', placeholder='How does the above code works?',
                               disabled=not uploaded_file and not input_text)

    if st.button('Ask', key='ask_button'):
        with st.session_state.agent(use_backup=False) as agent:
            with st.spinner('Thinking...'):
                prompt = f"{input_text}\n\n{query_text}\n\n"
                response = agent.respond(prompt)
                st.session_state.code_input = input_text
                st.session_state.query_text = query_text
                st.session_state.api.log(input_text, response, query_text, "Ask the Code App")
            st.write_stream(message_stream(response))
            st.session_state.result = response
