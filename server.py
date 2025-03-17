from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

LOCATION_FILE = "/home/TCMS/myapp/locations.json"

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

# Convert UTC to Pakistan Standard Time (PST)
def convert_to_pst(utc_time):
    utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    pst_dt = utc_dt + timedelta(hours=5)  # ✅ Add 5 hours for PST
    return pst_dt.strftime("%Y-%m-%d %I:%M:%S %p")  # ✅ Convert to readable format

# ✅ API to receive location data
@app.route('/send-location', methods=['POST'])
def receive_location():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    locations = load_data()

    # ✅ Assign Serial Number (Auto-increment)
    serial_number = len(locations) + 1
    data["serial_number"] = serial_number

    # ✅ Convert UTC timestamp to PST
    if "timestamp" in data:
        data["local_time_pst"] = convert_to_pst(data["timestamp"])

    locations.append(data)
    save_data(locations)

    return jsonify({"message": "Location received", "data": data})

# ✅ API to display locations in a table (Sorted & Paginated)
@app.route('/get-locations', methods=['GET'])
def get_locations():
    locations = load_data()

    # ✅ Sort locations (Most recent at the top)
    locations.reverse()

    # ✅ Pagination (Show 10 locations per page)
    page = int(request.args.get("page", 1))
    per_page = 10
    total_pages = (len(locations) // per_page) + (1 if len(locations) % per_page > 0 else 0)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = locations[start:end]

    # ✅ HTML structure for table
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Location Tracker</title>
    </head>
    <body>
        <h2>Live Location Data (Page {page}/{total_pages})</h2>
        <table border="1" cellspacing="0" cellpadding="5">
            <tr>
                <th>Serial No.</th>
                <th>Device ID</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Accuracy</th>
                <th>Timestamp (UTC)</th>
                <th>Local Time (PST)</th>
                <th>Device Info</th>
                <th>Google Maps</th>
            </tr>
    '''

    for loc in paginated_data:
        lat, lon = loc["latitude"], loc["longitude"]
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"

        html += f'''
        <tr>
            <td>{loc["serial_number"]}</td>
            <td>{loc.get("device_id", "Unknown")}</td>
            <td>{lat}</td>
            <td>{lon}</td>
            <td>{loc.get("accuracy", "N/A")}</td>
            <td>{loc["timestamp"]}</td>
            <td>{loc.get("local_time_pst", "N/A")}</td>
            <td>{loc.get("device_info", "N/A")}</td>
            <td><a href="{google_maps_url}" target="_blank">View on Google Maps</a></td>
        </tr>
        '''

    html += '''
        </table>
    '''

    # ✅ Pagination Links
    if page > 1:
        html += f'<a href="/get-locations?page={page-1}">Previous Page</a> '
    if page < total_pages:
        html += f' <a href="/get-locations?page={page+1}">Next Page</a>'

    html += '</body></html>'
    return html

if __name__ == "__main__":
    app.run(port=5000)  # Ensure the port is set to 5000
