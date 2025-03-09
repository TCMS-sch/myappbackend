from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

BASE_DIR = "/home/TCMS/myapp"
LOCATION_FILE = os.path.join(BASE_DIR, "locations.json")
UPDATE_REQUEST_FILE = os.path.join(BASE_DIR, "update_requests.json")

# Ensure the directory exists
os.makedirs(BASE_DIR, exist_ok=True)

# Ensure the files exist
for file in [LOCATION_FILE, UPDATE_REQUEST_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# Load existing data safely
def load_data(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
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

    locations[str(serial_number)] = data  # Store with string keys to ensure JSON compatibility
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
    if update_requests.get(device_id):
        update_requests[device_id] = False  # ✅ Mark as processed
        save_data(UPDATE_REQUEST_FILE, update_requests)
        return jsonify({"request_update": True})

    return jsonify({"request_update": False})

# ✅ API to display locations
@app.route('/get-locations', methods=['GET'])
def get_locations():
    locations = load_data(LOCATION_FILE)
    locations_list = sorted(locations.values(), key=lambda x: x.get("serial_number", 0), reverse=True)

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
    for loc in locations_list:
        google_maps_url = f"https://www.google.com/maps?q={loc.get('latitude', 'N/A')},{loc.get('longitude', 'N/A')}"
        html += f'''
        <tr>
            <td>{loc.get("serial_number", "N/A")}</td>
            <td>{loc.get("device_id", "N/A")}</td>
            <td>{loc.get("latitude", "N/A")}</td>
            <td>{loc.get("longitude", "N/A")}</td>
            <td>{loc.get("local_time_pst", "N/A")}</td>
            <td><a href="{google_maps_url}" target="_blank">View</a></td>
            <td><button onclick="fetch('/request-update', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{'device_id': '{loc.get('device_id', 'N/A')}'}}) }});">Request Update</button></td>
        </tr>
        '''
    html += '</table></body></html>'
    return html

if __name__ == '__main__':
    app.run(debug=True)
