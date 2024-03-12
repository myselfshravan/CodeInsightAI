import os
import streamlit as st
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()


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


# Page title
st.set_page_config(page_title='Ask the Code App', page_icon='🧑‍💻')

st.title('Ask the Code App')

st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)

input_text = st.text_area('Enter your code here:', placeholder='Please the code.', height=400)

uploaded_file = st.file_uploader('Upload the code', type=['py', 'js', 'jsx'], accept_multiple_files=True,
                                 key='file_uploader')
# Query text
query_text = st.text_input('Enter your question:', placeholder='Please provide a short summary.',
                           disabled=not uploaded_file)

# Form input and query
result = []
openai_api_key = os.getenv("OPENAI_API_KEY")
if st.button('Submit'):
    with st.spinner('Calculating...'):
        response = generate_response(uploaded_file, openai_api_key, query_text)
        result.append(response)
        del openai_api_key

if len(result):
    st.info(response)
