import os
import requests
from bs4 import BeautifulSoup

def download_files_from_repo(repo_url):
    base_url = 'https://github.com'

    response = requests.get(repo_url)
    html = response.content

    soup = BeautifulSoup(html, 'html.parser')

    a_tags = soup.find_all('a')
    links = [a.get('href') for a in a_tags]

    blob_links = [link for link in links if '/blob/' in link]

    download_folderpath = 'Desktop/down'  # Modified folder name
    desktop_path = os.path.join(os.path.expanduser('~'), download_folderpath)

    # Create the 'down' folder if it doesn't exist
    if not os.path.exists(desktop_path):
        os.makedirs(desktop_path)

    # Concatenate the downloaded text files
    with open(os.path.join(desktop_path, 'result.txt'), 'w') as result_file:
        for link in blob_links:
            raw_link = link.replace('/blob/', '/raw/')
            file_url = base_url + raw_link
            response = requests.get(file_url)
            file_name = raw_link.split('/')[-1]  # Remove .txt extension
            
            # Write the file name and content
            result_file.write(f"File: {file_name}\n\n")
            result_file.write(response.text)
            result_file.write("\n\n")  # Add two-line break

    print(f"Concatenated files saved to {download_folderpath}/result.txt")

repo_url = input("Enter Github Repo URL: ")
download_files_from_repo(repo_url)
