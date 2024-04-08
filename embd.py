import os
import requests
from bs4 import BeautifulSoup
import chromadb

def download_and_concatenate_files(repo_url, download_folderpath='Desktop/down'):
    base_url = 'https://github.com'
    response = requests.get(repo_url)
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    blob_links = [a.get('href') for a in soup.find_all('a') if '/blob/' in a.get('href', '')]

    desktop_path = os.path.join(os.path.expanduser('~'), download_folderpath)
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)

    result_file_path = os.path.join(desktop_path, 'result.txt')
    with open(result_file_path, 'w') as result_file:
        for link in blob_links:
            raw_link = link.replace('/blob/', '/raw/')
            file_url = base_url + raw_link
            file_response = requests.get(file_url)
            file_name = raw_link.split('/')[-1]
            result_file.write(f"File: {file_name}\n\n")
            result_file.write(file_response.text)
            result_file.write("\n\n")

    print(f"Concatenated files saved to {download_folderpath}/result.txt")
    return result_file_path

def generate_embeddings(filepath):
    with open(filepath, 'r') as file:
        content = file.read()
    return content  # In a real scenario, replace this with actual embedding generation

def store_in_database(data, collection_name="my_collection"):
    chroma_client = chromadb.Client()

    # Try to get the collection, create it if it doesn't exist
    try:
        collection = chroma_client.get_collection(name=collection_name)
        print(f"Collection '{collection_name}' already exists. Using the existing collection.")
    except Exception as e:
        print(f"Collection '{collection_name}' does not exist. Creating a new one.")
        collection = chroma_client.create_collection(name=collection_name)
        print(f"Collection '{collection_name}' created.")

    documents = data.split("\n\n\n")
    metadatas = [{"source": f"source_{i}"} for i, _ in enumerate(documents)]
    ids = [f"id_{i}" for i, _ in enumerate(documents)]
    collection.add(documents=documents, metadatas=metadatas, ids=ids)

    # Optional: Test query
    results = collection.query(query_texts=["Sample query"], n_results=2)
    print(results)

# Replace the placeholder with your actual GitHub repository URL
repo_url = "https://github.com/namratha-vj/daa-lab-programs"
concatenated_file_path = download_and_concatenate_files(repo_url)
embeddings = generate_embeddings(concatenated_file_path)
store_in_database(embeddings)
