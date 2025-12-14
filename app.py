from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'secret123'  # change this for production
CORS(app)

# 📦 MongoDB Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["sports_stats"]

users_col = db["users"]
players_col = db["players"]

# 🏠 Home Route
@app.route("/")
def home():
    return render_template("index.html")

# 📝 Signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        if users_col.find_one({"email": data["email"]}):
            return "Email already exists!"
        users_col.insert_one({
            "email": data["email"],
            "password": data["password"],
            "role": "user"
        })
        return redirect(url_for("user_login"))
    return render_template("signup.html")

# 🔑 Admin Login
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        data = request.form
        admin = users_col.find_one({"email": data["email"], "password": data["password"], "role": "admin"})
        if admin:
            session["email"] = admin["email"]
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        return "Invalid credentials"
    return render_template("admin_login.html")

# 🔑 User Login
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        data = request.form
        user = users_col.find_one({"email": data["email"], "password": data["password"], "role": "user"})
        if user:
            session["email"] = user["email"]
            session["role"] = "user"
            return redirect(url_for("user_dashboard"))
        return "Invalid credentials"
    return render_template("user_login.html")

# 🚪 Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# 🛠 Admin Dashboard
@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("home"))
    return render_template("admin_dashboard.html")

# 👤 User Dashboard
@app.route("/user_dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return redirect(url_for("home"))
    return render_template("user_dashboard.html")

# ➕ Add Player (Admin Only)
@app.route("/add_player/<sport>", methods=["POST"])
def add_player(sport):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    player = {
        "name": data["name"],
        "team": data["team"],
        "sport": sport,
        "stats": data.get("stats", {})  # dynamic per sport
    }
    players_col.insert_one(player)
    return jsonify({"message": "Player added!"}), 201

# 📄 Get Players by Sport (For Users)
@app.route("/get_players/<sport>")
def get_players(sport):
    players = list(players_col.find({"sport": sport}))
    for p in players:
        p["_id"] = str(p["_id"])
    return jsonify(players)


@app.route("/cricket")
def cricket():
    return render_template("cricket.html")

@app.route("/football")
def football():
    return render_template("football.html")

@app.route("/tennis")
def tennis():
    return render_template("tennis.html")

@app.route("/hockey")
def hockey():
    return render_template("hockey.html")


@app.route("/delete_player/<player_id>", methods=["DELETE"])
def delete_player(player_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    players_col.delete_one({"_id": ObjectId(player_id)})
    return jsonify({"message": "Deleted"}), 200


@app.route("/update_player/<player_id>", methods=["PUT"])
def update_player(player_id):
    if session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    data = request.json
    players_col.update_one(
        {"_id": ObjectId(player_id)},
        {"$set": {
            "name": data["name"],
            "team": data["team"],
            "stats": data.get("stats", {})
        }}
    )
    return jsonify({"message": "Updated"}), 200


if __name__ == "__main__":
    app.run(debug=True)
