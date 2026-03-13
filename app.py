from flask import Flask, render_template, request, jsonify, session
import sqlite3
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "medplantsecret"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

PLANTNET_API_KEY = "YOUR_PLANTNET_API_KEY"

# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------- SIGNUP ----------

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users(username,password) VALUES (?,?)",
                  (username,password))
        conn.commit()
        return jsonify({"status":"success"})
    except:
        return jsonify({"status":"exists"})

    finally:
        conn.close()


# ---------- LOGIN ----------

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username,password))
    user = c.fetchone()

    conn.close()

    if user:
        session["user"]=username
        return jsonify({"status":"success"})
    else:
        return jsonify({"status":"fail"})


# ---------- PLANT IDENTIFICATION ----------

@app.route("/predict", methods=["POST"])
def predict():

    if "user" not in session:
        return jsonify({"error":"login required"})

    file = request.files["image"]
    filename = secure_filename(file.filename)

    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    # ----- PlantNet API -----

    url = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"

    files = {"images": open(path,"rb")}
    data = {"organs":["leaf"]}

    response = requests.post(url, files=files, data=data)
    result = response.json()

    try:
        plant = result["results"][0]["species"]["scientificNameWithoutAuthor"]
    except:
        plant = "Unknown plant"

    # ----- Wikipedia description -----

    wiki = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{plant}"
    ).json()

    description = wiki.get("extract","No description available.")

    medicinal = "Medicinal uses vary. Consult botanical sources."

    return jsonify({
        "name":plant,
        "description":description,
        "medicinal":medicinal
    })


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)
