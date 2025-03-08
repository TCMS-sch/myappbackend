from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

LOCATION_FILE = "/home/TCMS/myapp/locations.json"
UPDATE_REQUEST_FILE = "/home/TCMS/myapp/update_requests.json"

# Ensure the files exist
for file in [LOCATION_FILE, UPDATE_REQUEST_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# Load existing data safely
def load_data(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save data safely
def save_data(file_path, data):
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print("Error saving data:", e)

# Convert UTC to Pakistan Standard Time (PST)
def convert_to_pst(utc_time):
    try:
        utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        pst_dt = utc_dt + timedelta(hours=5)
        return pst_dt.strftime("%Y-%m-%d %I:%M:%S %p")
    except Exception:
        return "Invalid Time"

# ✅ API to receive location data
@app.route('/send-location', methods=['POST'])
def receive_location():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    locations = load_data(LOCATION_FILE)
    serial_number = len(locations) + 1
    data["serial_number"] = serial_number

    if "timestamp" in data:
        data["local_time_pst"] = convert_to_pst(data["timestamp"])

    locations[serial_number] = data
    save_data(LOCATION_FILE, locations)

    return jsonify({"message": "Location received", "data": data})

# ✅ API to request a location update from a device
@app.route('/request-update', methods=['POST'])
def request_update():
    device_id = request.json.get("device_id")
    if not device_id:
        return jsonify({"error": "Device ID required"}), 400

    update_requests = load_data(UPDATE_REQUEST_FILE)
    update_requests[device_id] = True  # ✅ Mark this device for an update request
    save_data(UPDATE_REQUEST_FILE, update_requests)

    return jsonify({"message": "Update request sent to device", "device_id": device_id})

# ✅ API for child’s device to check if parent requested an update
@app.route('/check-update', methods=['GET'])
def check_update():
    device_id = request.args.get("device_id")
    if not device_id:
        return jsonify({"error": "Device ID required"}), 400

    update_requests = load_data(UPDATE_REQUEST_FILE)
    if device_id in update_requests and update_requests[device_id]:
        update_requests[device_id] = False  # ✅ Mark as processed
        save_data(UPDATE_REQUEST_FILE, update_requests)
        return jsonify({"request_update": True})

    return jsonify({"request_update": False})

# ✅ API to display locations
@app.route('/get-locations', methods=['GET'])
def get_locations():
    locations = load_data(LOCATION_FILE)
    locations = sorted(locations.values(), key=lambda x: x["serial_number"], reverse=True)

    html = '''
    <html><body>
    <h2>Live Location Data</h2>
    <table border="1">
        <tr>
            <th>Serial No.</th>
            <th>Device ID</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Local Time (PST)</th>
            <th>Google Maps</th>
            <th>Request Update</th>
        </tr>
    '''
    for loc in locations:
        google_maps_url = f"https://www.google.com/maps?q={loc['latitude']},{loc['longitude']}"
        html += f'''
        <tr>
            <td>{loc["serial_number"]}</td>
            <td>{loc["device_id"]}</td>
            <td>{loc["latitude"]}</td>
            <td>{loc["longitude"]}</td>
            <td>{loc.get("local_time_pst", "N/A")}</td>
            <td><a href="{google_maps_url}" target="_blank">View</a></td>
            <td><button onclick="fetch('https://tcms.pythonanywhere.com/request-update', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{'device_id': '{loc['device_id']}'}}) }});">Request Update</button></td>
        </tr>
        '''
    html += '</table></body></html>'
    return html
