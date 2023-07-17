from flask import Flask, render_template, jsonify, request
from flask_mqtt import Mqtt
app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = '192.168.11.53'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'flask_mqtt'
app.config['MQTT_CLEAN_SESSION'] = True

mqtt = Mqtt(app)

# Data storage
table_one = []
table_two = []


@app.route('/')
def index():
    return render_template('index2.html')


@app.route('/api/table-one', methods=['GET'])
def get_table_one():
    return jsonify(table_one)


@app.route('/api/table-two', methods=['GET'])
def get_table_two():
    return jsonify(table_two)


@app.route('/api/assign-number', methods=['POST'])
def assign_number():
    mac_address = request.json['mac_address']
    bay_number = request.json['bay_number']

    # Publish MQTT message with assigned bay number
    mqtt.publish('mac_addresses', f'{mac_address}:{bay_number}')

    # Move entry from Table one to Table two
    table_one.remove(mac_address)
    table_two.append({'mac_address': mac_address, 'bay_number': bay_number, 'status': 'Assigned'})

    return jsonify({'success': True})


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    payload = message.payload.decode()
    mac_address, bay_number = payload.split(':')

    # Store data in Table one
    table_one.append(mac_address)

    # Send Table one and Table two updates to clients
    mqtt.publish('table_one_update', mac_address)
    mqtt.publish('table_two_update', f'{mac_address}:{bay_number}')


if __name__ == '__main__':
    mqtt.subscribe('mac_addresses')
    app.run(debug=True)
