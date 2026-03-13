from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DATABASE
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

# SIGNUP
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username,password) VALUES (?,?)",(username,password))
        conn.commit()
        return jsonify({"status":"success"})
    except:
        return jsonify({"status":"user_exists"})
    finally:
        conn.close()


# LOGIN
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    user = c.execute("SELECT * FROM users WHERE username=? AND password=?",
                     (username,password)).fetchone()

    conn.close()

    if user:
        return jsonify({"status":"success"})
    else:
        return jsonify({"status":"invalid"})


# PLANT IDENTIFICATION
def identify_plant(image_path):

    url = "https://my-api.plantnet.org/v2/identify/all?api-key=demo"

    files = {
        "images": open(image_path, "rb")
    }

    res = requests.post(url, files=files)

    data = res.json()

    try:
        return data["results"][0]["species"]["scientificNameWithoutAuthor"]
    except:
        return "Unknown plant"


# WIKIPEDIA DATA
def get_wikipedia_data(plant):

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{plant}"

    r = requests.get(url)

    if r.status_code == 200:
        data = r.json()
        desc = data.get("extract","No description available.")
    else:
        desc = "No information found."

    medicinal = f"Medicinal uses of {plant} may include traditional herbal treatments. Consult scientific sources for detailed pharmacological effects."

    return desc, medicinal


# UPLOAD IMAGE
@app.route("/predict", methods=["POST"])
def predict():

    file = request.files["image"]

    filename = secure_filename(file.filename)

    path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(path)

    plant = identify_plant(path)

    description, medicinal = get_wikipedia_data(plant)

    return jsonify({
        "scientific_name": plant,
        "description": description,
        "medicinal": medicinal
    })


if __name__ == "__main__":
    app.run(debug=True)
