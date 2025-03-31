from flask import Flask, render_template, request, jsonify
from services.gutenberg_ebook import *
from services.operations import json_to_html_table, get_all_books

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
    contents = proccess_gutenberg(book_id)
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
    
    if not book_id or not analysis_type:
        return jsonify({"error": "Book ID and analysis type are required"}), 400
    if book_id not in books:
        return jsonify({"error": "Book not found"}), 404
    
    response = {
        "bookId": book_id,
        "type": analysis_type,
        "result": f"Dummy analysis result for {analysis_type}"
    }
    return jsonify(response)

@app.route("/get_all_ebooks", methods=["GET"])
def get_all_books_html():
    books_data = get_all_books()
    print(books_data)
    return jsonify(books_data)

if __name__=="__main__":
    app.run(debug=True)