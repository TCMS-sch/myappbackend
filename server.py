from flask import Flask, request, jsonify
import json
import datetime

app = Flask(__name__)

# File to store locations
LOCATION_FILE = "locations.json"

# Load existing data
def load_data():
    try:
        with open(LOCATION_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Save data to file
def save_data(data):
    with open(LOCATION_FILE, "w") as file:
        json.dump(data, file, indent=4)

@app.route('/send-location', methods=['POST'])
def receive_location():
    data = request.json
    data["timestamp"] = str(datetime.datetime.now())  # Add timestamp

    # Load and update data
    locations = load_data()
    locations.append(data)
    save_data(locations)

    return jsonify({"message": "Location received successfully!", "data": data})

@app.route('/get-locations', methods=['GET'])
def get_locations():
    return jsonify(load_data())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
