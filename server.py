from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)  # ✅ Define Flask app BEFORE using @app.route

# File to store locations
LOCATION_FILE = "/home/TCMS/myapp/locations.json"  # ✅ Ensure this path is correct

# Ensure the file exists
if not os.path.exists(LOCATION_FILE):
    with open(LOCATION_FILE, "w") as file:
        json.dump([], file)

# Load existing data
def load_data():
    try:
        with open(LOCATION_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Save data
def save_data(data):
    with open(LOCATION_FILE, "w") as file:
        json.dump(data, file, indent=4)

# ✅ Home route (fixes "Not Found" error)
@app.route('/')
def home():
    return "Flask App is Running! Use /send-location to send data and /get-locations to retrieve it."

# ✅ API to receive location data
@app.route('/send-location', methods=['POST'])
def receive_location():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    locations = load_data()
    locations.append(data)
    save_data(locations)

    return jsonify({"message": "Location received", "data": data})

# ✅ API to fetch stored locations
@app.route('/get-locations', methods=['GET'])
def get_locations():
    return jsonify(load_data())

