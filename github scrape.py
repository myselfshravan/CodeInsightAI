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

 download_folderpath = 'Desktop'
 desktop_path = os.path.join(os.path.expanduser('~'), download_folderpath)

 for link in blob_links:
    raw_link = link.replace('/blob/', '/raw/')
    file_url = base_url + raw_link
    file_path = raw_link.split('/')
    file_name = file_path[-1]+'.txt'
    download_path = os.path.join(desktop_path, *file_path[:-1])
    
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    
    response = requests.get(file_url)
    with open(os.path.join(download_path, file_name), 'wb') as f:
        f.write(response.content)
        print(f"File '{file_name}' downloaded to ",download_folderpath)

repo_url=input("Enter Github Repo URL: ")
download_files_from_repo(repo_url)