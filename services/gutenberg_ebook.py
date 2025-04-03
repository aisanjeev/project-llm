import requests
from bs4 import BeautifulSoup
import os
from groq import Groq
from .operations import *
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def getGroqClient():
    client = Groq(
        api_key=os.getenv('API_KEY'),
    )
    return client
def scrape_gutenberg_metadata(book_id):
    """
    Scrape metadata from a Project Gutenberg eBook page.

    Parameters:
    book_id (int): The unique identifier of the eBook on Project Gutenberg.

    Returns:
    dict, int: A dictionary containing the scraped metadata and the HTTP status code.
               If the book is not found, the dictionary will contain an "error" key with the value "ebook not found",
               and the status code will be 404.
               If any other request failure occurs, the dictionary will contain the error message,
               and the status code will be 500.
               If the request is successful, the dictionary will contain the scraped metadata, and the status code will be 200.
    """
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
        return {"error": str(e)}, 500  # Return 500 for any other request failures


def get_ebook_data(book_id):
    """
    Fetch book content from Project Gutenberg and save it as a text file.

    If the first attempt fails, retry once by removing '-0' from the URL.
    If both attempts fail, save "Ebook content not found".

    Parameters:
    book_id (int): The unique identifier of the eBook on Project Gutenberg.

    Returns:
    tuple: A tuple containing the file path and the content of the eBook.
           If both attempts to fetch the content fail, the content will be "Ebook content not found".
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
    """
    Processes an eBook from Project Gutenberg.

    This function checks if the eBook with the given book_id already exists in the database.
    If it does, the function retrieves the eBook content from the local file.
    If it doesn't, the function scrapes the eBook metadata from Project Gutenberg,
    fetches the eBook content, saves it as a text file, and inserts the data into the database.

    Parameters:
    book_id (int): The unique identifier of the eBook on Project Gutenberg.

    Returns:
    tuple: A tuple containing the eBook content and the file path.
           If the eBook content is not found, the content will be "Ebook content not found".
    """
    if_exist, file_path = book_id_exists(book_id)
    if if_exist:
        content = read_txt_file(book_id)
        return content, file_path

    print("bookid", book_id)
    metas, status = scrape_gutenberg_metadata(book_id)
    print(metas)
    content = "Ebook content not found"  # Default content in case of failure

    if status == 200:
        file_path, content = get_ebook_data(book_id)
        print(file_path)
        insert_ebook_data(book_id, metas, txt_path=file_path)

    return content, file_path


def search_gutenberg(book_id):
    """
    Search for an eBook in the local database based on its unique identifier.

    Parameters:
    book_id (int): The unique identifier of the eBook on Project Gutenberg.

    Returns:
    str, bytes: If the eBook is found in the database, the function returns the content of the eBook.
                If the eBook is not found, the function returns the string "Data not found".
    """
    if_exist, file_path = book_id_exists(book_id)
    if if_exist:
        content = read_txt_file(book_id)
        return content
    return "Data not found"


def process_analysis(file_path, book_id):
    """
    Performs a comprehensive analysis of an eBook using the Groq API.

    This function reads the text content of an eBook from a local file,
    inserts a new eBook record into the database with a pending status,
    chunks the text into smaller segments, selects a subset of these chunks for analysis,
    sends the selected chunks to the Groq API for raw analysis,
    merges the responses from the Groq API, processes the final analysis,
    extracts relevant information from the processed analysis,
    updates the eBook record in the database with the analysis results,
    and returns True upon successful completion.

    Parameters:
    file_path (str): The file path of the local text file containing the eBook content.
    book_id (int): The unique identifier of the eBook in the database.

    Returns:
    bool: True if the analysis is completed successfully, False otherwise.
    """
    text = read_txt_file(book_id)
    # Insert new ebook (Pending status)
    isexit, data = book_id_exists_in_analysis(book_id)
    if isexit and data[-1] != "In Progress":
        return data
    insert_ebook(book_id)
    chunk = chunk_text(text, max_length=5000)
    print("chunk len", len(chunk))
    selected_chunks = select_chunks(chunk, num_samples=10)
    print("selected_chunks len", len(selected_chunks))
    client=getGroqClient()
    summary = process_raw_analysis(client, selected_chunks)
    merged_output = merge_responses(summary)
    client=getGroqClient()
    print("merged_output", merged_output)
    raw_json_output = process_final_analysis(merged_output, client)
    print("raw_json_output", raw_json_output)
    final_analysis = extract_json(raw_json_output)
    print("final_analysis", final_analysis)
    # print(final_analysis)
    try:
        update_ebook_data(
            ebook_id=book_id,
            summary=final_analysis.get("summary", ""),
            sentiment=final_analysis.get("sentiment", ""),
            language=final_analysis.get("language", ""),
            key_characters=final_analysis.get("key_characters", ""),
            themes=final_analysis.get("key_characters", "themes"),
            status="Analysis Completed"
        )
    except Exception as e:
        update_ebook_data(
            ebook_id=book_id,
            summary="",
            sentiment="",
            language="",
            key_characters="",
            themes="",
            status="Analysis Failed"
        )
    return True

