from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import requests

app = Flask(__name__)

API_KEY = "YOUR_PLANTNET_API_KEY"

# -----------------------
# Database
# -----------------------

def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------
# Serve frontend
# -----------------------

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def css():
    return send_from_directory(".", "style.css")

@app.route("/script.js")
def js():
    return send_from_directory(".", "script.js")

# -----------------------
# Signup
# -----------------------

@app.route("/signup", methods=["POST"])
def signup():

    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users(username,password) VALUES (?,?)",
        (username,password)
    )

    conn.commit()
    conn.close()

    return jsonify({"message":"Signup successful"})


# -----------------------
# Login
# -----------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    )

    user = cur.fetchone()

    conn.close()

    if user:
        return jsonify({"message":"Login successful"})
    else:
        return jsonify({"message":"Invalid credentials"}),401


# -----------------------
# Plant Identification
# -----------------------

@app.route("/identify", methods=["POST"])
def identify():

    image = request.files["image"]

    files = {
        "images": (image.filename, image.stream, image.mimetype)
    }

    data = {"organs":"leaf"}

    url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

    response = requests.post(url, files=files, data=data)
    result = response.json()

    try:

        plant = result["results"][0]

        scientific = plant["species"]["scientificNameWithoutAuthor"]

        description = plant["species"]["genus"]["scientificName"]

        uses = """
Leaves: Used in herbal medicine  
Roots: Used in traditional remedies  
Bark: Anti-inflammatory properties
"""

        return jsonify({
            "scientific": scientific,
            "description": description,
            "uses": uses
        })

    except:
        return jsonify({"error":"Plant not identified"})


if __name__ == "__main__":
    app.run(debug=True)
