from flask import Flask, render_template, request, jsonify
from services.gutenberg_ebook import *
import threading
from services.operations import *

create_database()
app= Flask(__name__)
books = {
    "1234": "This is a sample text for book ID 123.",
    "456": "Another example book with different content."
}


@app.route("/")
def home():
    return render_template("index.html")
def get_book(book_id):
    """Helper function to fetch book content by ID."""
    return books.get(book_id)

@app.route("/fetch_book", methods=["GET"])
def fetch_book():
    book_id = request.args.get("bookId")
    contents, file_path = proccess_gutenberg(book_id)
    insert_ebook(book_id)
    # Run process_analysis in a background thread
    thread = threading.Thread(target=process_analysis, args=(file_path, book_id))
    thread.start()
    return jsonify({"bookId": book_id, "content": contents})

@app.route("/search", methods=["GET"])
def search_book():
    query = request.args.get("query", "").strip().lower()
    data = search_gutenberg(query)
    return jsonify({"content": data})

@app.route("/analyze", methods=["POST"])
def analyze_text():
    data = request.get_json()
    book_id = data.get("bookId")
    analysis_type = data.get("type")
    ifexits, record = book_id_exists_in_analysis(book_id)
    if not book_id or not analysis_type:
        return jsonify({"error": "Book ID and analysis type are required"}), 400
    if ifexits:
        result = ebook_analysis_to_html(record)
        response = {
            "bookId": book_id,
            "type": analysis_type,
            "result": f"{result}"
        }
        return jsonify(response)
    else:
        return jsonify({"result": "Ebook is not valid!"})

@app.route("/get_all_ebooks", methods=["GET"])
def get_all_books_html():
    books_data = get_all_books()
    print(books_data)
    return jsonify(books_data)

if __name__=="__main__":
    app.run(debug=True, port=5005, host="0.0.0.0")