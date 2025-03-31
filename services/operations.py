import json
import sqlite3

def json_to_html_table(json_data):
    """Converts JSON data to an HTML table with Tailwind CSS."""
    
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
    Check if a book with the given ID exists in the database."
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM ebooks WHERE book_id =?"
    cursor.execute(query, (book_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None
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

def read_txt_file(file_path):
    """Read content from a text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "Error: File not found."
    except Exception as e:
        return f"Error reading file: {e}"

