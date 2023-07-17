from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT configurations
MQTT_BROKER = "localhost"
MQTT_TOPIC = "mac_addresses"

# Data storage
unassigned_mac_addresses = []
assigned_mac_addresses = []

# Connect to MQTT broker
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/unassigned-mac-addresses")
def get_unassigned_mac_addresses():
    return jsonify(unassigned_mac_addresses)


@app.route("/api/assigned-mac-addresses")
def get_assigned_mac_addresses():
    return jsonify(assigned_mac_addresses)


@app.route("/api/assign-bay", methods=["POST"])
def assign_bay():
    mac_address = request.json["mac_address"]
    bay_number = request.json["bay_number"]

    # Publish MQTT message with assigned bay number
    mqtt_client.publish(MQTT_TOPIC, f"{mac_address}:{bay_number}")

    # Move entry from unassigned to assigned
    entry = next(filter(lambda x: x["mac_address"] == mac_address, unassigned_mac_addresses), None)
    if entry:
        entry["bay_number"] = bay_number
        entry["status"] = "Assigned"
        assigned_mac_addresses.append(entry)
        unassigned_mac_addresses.remove(entry)

    return jsonify({"success": True})


@app.route("/api/mqtt-message", methods=["POST"])
def handle_mqtt_message():
    mac_address = request.json["mac_address"]
    bay_number = request.json.get("bay_number")

    if bay_number is None:
        entry = next(filter(lambda x: x["mac_address"] == mac_address, unassigned_mac_addresses), None)
        if entry is None:
            unassigned_mac_addresses.append({"mac_address": mac_address})
    else:
        assigned_mac_addresses.append({"mac_address": mac_address, "bay_number": bay_number, "status": "Assigned"})

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
