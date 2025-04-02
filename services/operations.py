import json
import sqlite3
import random
import re
from collections import defaultdict

def ebook_analysis_to_html(row):
    """
    Converts an ebook_analysis row into a styled Tailwind HTML string.

    Parameters:
    row (sqlite3.Row): A row from the ebook_analysis table.

    Returns:
    str: A string containing the styled HTML for the ebook details.
    """
    if not row:
        return """<div class="text-red-600 font-semibold p-4">No data found for the given Book ID.</div>"""

    # Extract values from the row
    ebook_id, summary, sentiment, language, key_characters, themes, status = row[1:]

    # Convert JSON fields to formatted strings
    key_characters_list = json.loads(key_characters) if key_characters else []
    themes_list = json.loads(themes) if themes else []

    key_characters_html = ", ".join(f"<span class='px-2 py-1 bg-gray-200 rounded-lg'>{char}</span>" for char in key_characters_list)
    themes_html = ", ".join(f"<span class='px-2 py-1 bg-blue-200 rounded-lg'>{theme}</span>" for theme in themes_list)

    # Construct HTML
    html_content = f"""
    <div class="max-w-3xl w-full bg-white">
        <h2 class="text-2xl font-bold text-gray-800 mb-4">📖 EBook Details</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="font-semibold text-gray-600">📌 Ebook ID:</div>
            <div class="text-gray-800">{ebook_id}</div>

            <div class="font-semibold text-gray-600">📜 Summary:</div>
            <div class="text-gray-800 text-sm leading-relaxed">{summary}</div>

            <div class="font-semibold text-gray-600">📊 Sentiment:</div>
            <div class="text-gray-800">{sentiment}</div>

            <div class="font-semibold text-gray-600">🌎 Language:</div>
            <div class="text-gray-800">{language}</div>

            <div class="font-semibold text-gray-600">🎭 Key Characters:</div>
            <div class="flex flex-wrap gap-2">{key_characters_html}</div>

            <div class="font-semibold text-gray-600">🎨 Themes:</div>
            <div class="flex flex-wrap gap-2">{themes_html}</div>

            <div class="font-semibold text-gray-600">📌 Status:</div>
            <div class="text-gray-800 font-semibold text-lg">{status}</div>
        </div>
    </div>
    """

    return html_content


def json_to_html_table(json_data):
    """
    Converts JSON data to an HTML table with Tailwind CSS.

    Parameters:
    json_data (dict): A dictionary containing the JSON data to be converted into an HTML table.

    Returns:
    str: A string representing the HTML code for the table.
    """
    table_html = """
        <div class="max-w-2xl w-full bg-white shadow-lg rounded-lg p-6">
            <h2 class="text-2xl font-bold text-gray-700 mb-4">EBook Meta Data</h2>
            <table class="w-full border border-gray-300 rounded-lg">
                <tbody>
    """

    for key, value in json_data.items():
        table_html += f"""
        <tr class="border-b border-gray-200">
            <th class="text-left px-4 py-2 font-semibold bg-gray-100">{key}</th>
            <td class="px-4 py-2">{value}</td>
        </tr>
        """

    table_html += """
                </tbody>
            </table>
        </div>
    """

    return table_html


# Database connection function
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection

def create_database():
    """Creates the ebook_analysis table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ebook_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ebook_id INTEGER NOT NULL UNIQUE,
        summary TEXT,
        sentiment TEXT,
        language TEXT,
        key_characters TEXT,  -- Store as JSON string
        themes TEXT,          -- Store as JSON string
        status TEXT NOT NULL
    )
    ''')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ebook_json TEXT NULL,
        book_id TEXT NULL,
        txt_path TEXT NULL,
        accessed_date DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

def insert_ebook(ebook_id):
    """Inserts a new record with only ebook_id and status='pending'."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO ebook_analysis (ebook_id, status)
        VALUES (?, ?)
        ''', (ebook_id, "In Progress"))

        conn.commit()
        print(f"Record created with ebook_id={ebook_id}, status='In Progress'")
    except sqlite3.IntegrityError:
        print(f"Record with ebook_id={ebook_id} already exists.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def update_ebook_data(ebook_id, summary, sentiment, language, key_characters, themes, status):
    """Updates an existing record with full details based on ebook_id."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Convert lists to JSON strings
        key_characters_json = json.dumps(key_characters)
        themes_json = json.dumps(themes)

        cursor.execute('''
        UPDATE ebook_analysis 
        SET summary=?, sentiment=?, language=?, key_characters=?, themes=?, status=? 
        WHERE ebook_id=?
        ''', (summary, sentiment, language, key_characters_json, themes_json, status, ebook_id))

        if cursor.rowcount == 0:
            print(f"No record found for ebook_id={ebook_id}")
        else:
            print(f"Record updated successfully for ebook_id={ebook_id}")

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

# create_database()


# Function to insert ebook data
def insert_ebook_data(book_id, data, txt_path=None):
    """
    Insert ebook metadata into the database as JSON.

    Parameters:
    data (dict): A dictionary containing the ebook metadata. Each key-value pair represents a metadata field and its value.
    txt_path (str, optional): The path to the text file associated with the ebook. Defaults to None.

    Returns:
    None

    This function converts the provided ebook metadata dictionary into a JSON string, establishes a connection to the SQLite database,
    ensures the existence of the 'ebooks' table, inserts the JSON string and the optional text file path into the table,
    commits the changes, and closes the database connection.
    """
    # Convert dictionary to JSON string
    ebook_json = json.dumps(data)

    # Get a database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure the table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ebook_json TEXT NULL,
        book_id TEXT NULL,
        txt_path TEXT NULL,
        accessed_date DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Insert data into the table
    insert_query = "INSERT INTO ebooks (book_id, ebook_json, txt_path) VALUES (?, ?, ?)"
    cursor.execute(insert_query, (book_id, ebook_json, txt_path))

    # Commit and close the connection
    conn.commit()
    conn.close()

    print("Ebook data inserted successfully!")

def book_id_exists(book_id):
    """
    Check if a book with the given ID exists in the database.
    Returns a tuple (exists, value) where 'exists' is a boolean
    and 'value' is row[3] if available, else None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM ebooks WHERE book_id = ?"
    cursor.execute(query, (book_id,))
    row = cursor.fetchone()
    conn.close()
    
    return (row is not None, row[3] if row else None)
def book_id_exists_in_analysis(book_id):
    """
    Check if a book with the given ID exists in the database.
    Returns a tuple (exists, value) where 'exists' is a boolean
    and 'value' is row[3] if available, else None.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM ebook_analysis WHERE ebook_id = ?"
    cursor.execute(query, (book_id,))
    row = cursor.fetchone()
    conn.close()
    
    return (row is not None, row if row else None)
def get_all_books():
    """
    Fetch all books from the database and return as a list of dictionaries.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT book_id FROM ebooks"
    cursor.execute(query)
    rows = cursor.fetchall()
    
    conn.close()
    
    # Convert the rows to a list of dictionaries
    books = [{"Book_id": row[0]} for row in rows]
    
    return books

def read_txt_file(ebook_id):
    """Read content from a text file."""
    file_path = "uploads/"+ebook_id+".txt"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error reading file: {e}"

def chunk_text(text, max_length=5000):
    """Splits the text into chunks of specified max_length."""
    chunks = []
    while len(text) > max_length:
        split_index = text[:max_length].rfind(".") + 1
        if split_index == 0:
            split_index = max_length
        chunks.append(text[:split_index].strip())
        text = text[split_index:].strip()
    chunks.append(text)
    return chunks

def select_chunks(chunks, num_samples=20):
    """Selects a subset of chunks, ensuring diversity from start, middle, and end."""
    if len(chunks) <= num_samples:
        return chunks  # If chunks are fewer than needed, return all
    
    start_chunks = chunks[:max(1, num_samples // 4)]  # First few chunks
    end_chunks = chunks[-max(1, num_samples // 4):]  # Last few chunks
    middle_chunks = chunks[max(1, len(chunks) // 3): -max(1, len(chunks) // 3)]  # Middle section
    
    if len(middle_chunks) > num_samples - len(start_chunks) - len(end_chunks):
        middle_chunks = random.sample(middle_chunks, num_samples - len(start_chunks) - len(end_chunks))
    
    return start_chunks + middle_chunks + end_chunks

def process_raw_analysis(client, selected_chunks):
    summary = []
    for i in selected_chunks:
        prompt = (
                    "You are a highly intelligent AI assistant specializing in summarizing eBooks with precision and clarity. "
                    "Your task is to extract key points, main ideas, and crucial details while ensuring coherence and brevity.\n\n"
                    "Begin the response by analyzing and providing:\n"
                    "At the begining of response just inlcude json response only"
                    "- The overall sentiment of the text (e.g., positive, neutral, negative).\n"
                    "- The language in which the text is written.\n"
                    "- Identification of key characters (if applicable).\n\n"
                    "Then, generate a well-structured and highly concise summary that captures all essential points without losing meaning.\n\n"
                    "The response should be in a structured JSON format as follows:\n\n"
                    "{\n"
                    '  "summary": "...",\n'
                    '  "sentiment": "...",\n'
                    '  "language": "...",\n'
                    '  "key_characters": ["...", "..."],\n'
                    '  "themes": ["...", "..."]\n'
                    "}\n"
                    "\nNow, process the following text and generate the response:\n\n" + i
            )
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "you are a helpful assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5
        )
        print(chat_completion.choices[0].message.content)
        summary.append(chat_completion.choices[0].message.content)
    return summary

def extract_json(raw_string):
    """Extract JSON content from a string enclosed within triple backticks."""
    json_match = re.search(r"```(.*?)```", raw_string, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    return None

def merge_responses(response_list):
    """Merge multiple JSON responses into a single structured dictionary."""
    merged_data = defaultdict(list)
    
    for raw_response in response_list:
        parsed_json = extract_json(raw_response)
        if parsed_json:
            for key, value in parsed_json.items():
                if isinstance(value, list):
                    merged_data[key].extend(value)
                elif isinstance(value, str):
                    merged_data[key].append(value)
                else:
                    merged_data[key].append(str(value))
    
    # Convert lists to properly formatted values
    final_data = {}
    for key, value in merged_data.items():
        if key in ["summary", "sentiment", "language"]:
            final_data[key] = " ".join(value)  # Join string fields
        else:
            final_data[key] = list(set(value))  # Remove duplicates for lists
    
    return final_data

def process_final_analysis(merged_output, client):
    prompt = (
    "You are an advanced AI designed to process and refine text data with clarity and conciseness. "
    "Your task is to analyze the provided summaries and generate a refined version that meets the following criteria:\n\n"
    "1. Provide a well-structured and concise summary that retains all essential points while improving readability.\n"
    "2. Identify and consolidate sentiments—if duplicates exist, remove them; if they are similar, retain only the most relevant one.\n"
    "3. Identify and consolidate the language—if duplicates exist, remove them; if they are similar, retain only one.\n"
    "4. Extract key characters, ensuring no duplicates while keeping only distinct names.\n"
    "5. Extract themes, removing exact duplicates but preserving variations when necessary.\n\n"
    "6. Response should have only my json nothing else"
    "The output should be in structured JSON format as follows:\n\n"
    "{\n"
    '  "summary": "...",\n'
    '  "sentiment": "...",\n'
    '  "language": "...",\n'
    '  "key_characters": ["...", "..."],\n'
    '  "themes": ["...", "..."]\n'
    "}\n\n"
    "Now, process the following text and generate the response:\n\n" + str(merged_output)
    )

    # AI Processing (Example usage, requires an AI API like OpenAI, Groq, etc.)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.5
    )

    return chat_completion.choices[0].message.content