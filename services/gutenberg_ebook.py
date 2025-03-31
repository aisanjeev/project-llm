import requests
from bs4 import BeautifulSoup
import json
import os
from .operations import *
def scrape_gutenberg_metadata(book_id):
    """Scrape metadata from a Project Gutenberg eBook page."""
    url = f"https://www.gutenberg.org/ebooks/{book_id}"

    try:
        response = requests.get(url)
        
        # If the book is not found, return 404
        if response.status_code == 404:
            return {"error": "ebook not found"}, 404

        response.raise_for_status()  # Raise an error for other bad responses (e.g., 500)

        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find('table', class_='bibrec')
        metadata = {}

        if table:
            for row in table.find_all('tr'):
                th = row.find('th')  # Get the header column
                td = row.find('td')  # Get the value column
                
                if th and td:  # Ensure both elements exist
                    header = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    metadata[header] = value

        return metadata, 200
    
    except requests.exceptions.RequestException as e:
        return "Request failed to load ebook", 500  # Return 500 for any other request failures


def get_ebook_data(book_id):
    """Fetch book content from Project Gutenberg and save it as a text file.
    
    If the first attempt fails, retry once by removing '-0' from the URL.
    If both attempts fail, save "Ebook content not found".
    """
    # Primary URL format
    content_urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt"  # Retry without "-0"
    ]
    print(content_urls)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)  # Ensure upload directory exists

    file_path = os.path.join(upload_dir, f"{book_id}.txt")

    content = "Ebook content not found"  # Default content in case of failure

    for url in content_urls:
        print(url)
        try:
            response = requests.get(url)
            
            response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
            content = response.text
            break  # Exit loop if request succeeds
        except requests.exceptions.RequestException:
            continue  # Try the next URL if the first one fails

    # Save content to file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    return file_path, content  # Return file path and content

def proccess_gutenberg(book_id):
    if_exist = book_id_exists(book_id)
    if if_exist:
        path = "uploads/" + book_id + ".txt"
        content = read_txt_file(path)
        return content
    print("bookid", book_id)
    metas, status =  scrape_gutenberg_metadata(book_id)
    print(metas)
    content = "Ebook content not found"  # Default content in case of failure
    if status==200:
        file_path, content = get_ebook_data(book_id)
        print(file_path)
        insert_ebook_data(book_id, metas, txt_path=file_path)
    return content

def search_gutenberg(book_id):
    if_exist = book_id_exists(book_id)
    if if_exist:
        path = "uploads/" + book_id + ".txt"
        content = read_txt_file(path)
        return content
    return "Data not found"