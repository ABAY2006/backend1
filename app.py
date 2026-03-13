from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import requests

app = Flask(__name__)

API_KEY = "YOUR_PLANTNET_API_KEY"

# -----------------------
# DATABASE SETUP
# -----------------------

def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------
# SERVE FRONTEND
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
# SIGNUP
# -----------------------

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message":"Username and password required"}),400

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    try:

        cur.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (username,password)
        )

        conn.commit()

        return jsonify({"message":"Signup successful"})

    except sqlite3.IntegrityError:
        return jsonify({"message":"User already exists"})

    finally:
        conn.close()


# -----------------------
# LOGIN
# -----------------------

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

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
        return jsonify({"message":"Invalid username or password"}),401


# -----------------------
# PLANT IDENTIFICATION
# -----------------------

@app.route("/identify", methods=["POST"])
def identify():

    if "image" not in request.files:
        return jsonify({"error":"No image uploaded"})

    image = request.files["image"]

    files = {
        "images": (image.filename, image.stream, image.mimetype)
    }

    data = {"organs":"leaf"}

    url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

    try:

        response = requests.post(url, files=files, data=data)
        result = response.json()

        plant = result["results"][0]

        scientific = plant["species"]["scientificNameWithoutAuthor"]

        description = plant["species"]["genus"]["scientificName"]

        uses = """
Leaves: Used in herbal medicine  
Roots: Used in traditional remedies  
Bark: Anti-inflammatory properties
"""

        return jsonify({
            "scientific":scientific,
            "description":description,
            "uses":uses
        })

    except:
        return jsonify({"error":"Plant not identified"})


# -----------------------

if __name__ == "__main__":
    app.run(debug=True)
