// static/js/main.js

let thermohygrometerConnections = {};
const RECONNECT_DELAY = 5000;
const MAX_RECONNECT_ATTEMPTS = 3;

document.addEventListener('DOMContentLoaded', async function () {
    try {
        // Aqui devemos usar a URL normal, não a de conectados, pois queremos listar todos
        const response = await fetch('/api/v1/thermohygrometers/');
        const thermohygrometers = await response.json();
        const dropdown = document.getElementById('thermohygrometer');
        thermohygrometers.forEach(thermo => {
            const option = document.createElement('option');
            option.value = thermo.id;
            option.textContent = `${thermo.instrument_name} - PN: ${thermo.pn}, SN: ${thermo.sn}`;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching thermohygrometers:', error);
    }
});

async function addThermohygrometer() {
    const dropdown = document.getElementById('thermohygrometer');
    const selectedThermohygrometer = dropdown.value;
    const selectedInstrumentName = dropdown.options[dropdown.selectedIndex].text;

    if (thermohygrometerConnections[selectedThermohygrometer]) {
        alert('This thermohygrometer is already connected.');
        return;
    }

    const resultContainer = document.getElementById('result-container');
    const resultDiv = document.createElement('div');
    resultDiv.id = `result-${selectedThermohygrometer}`;
    resultDiv.className = 'result';
    const [thermoName, thermoPNSN] = selectedInstrumentName.split(' - ');

    const connectingMessage = document.createElement('p');
    connectingMessage.textContent = 'Connecting...';
    resultDiv.appendChild(connectingMessage);
    const resultHeader = document.createElement('h3');
    resultHeader.textContent = thermoName;
    resultDiv.appendChild(resultHeader);

    const resultSubHeader = document.createElement('p');
    resultSubHeader.textContent = thermoPNSN;
    resultDiv.appendChild(resultSubHeader);

    resultContainer.appendChild(resultDiv);

    // Create a container for sensors
    const sensorsContainer = document.createElement('div');
    sensorsContainer.className = 'sensors-container';
    sensorsContainer.id = `sensors-${selectedThermohygrometer}`;
    resultDiv.appendChild(sensorsContainer);

    let reconnectAttempts = 0;

    function createWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/data/${selectedThermohygrometer}/`);

        thermohygrometerConnections[selectedThermohygrometer] = ws;

        ws.onopen = function () {
            console.log(`WebSocket connection opened for ${selectedInstrumentName}`);
            if (resultDiv.contains(connectingMessage)) {
                resultDiv.removeChild(connectingMessage);
            }
        };

        ws.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.error) {
                console.log(data.error);
                return;
            }

            if (!data.data) {
                console.log(`No data received for ${selectedInstrumentName}`);
                return;
            }
            
            // Get sensor data
            const sensorData = data.data;
            const sensorId = sensorData.sensor_id;
            const sensorName = sensorData.sensor_name;
            const location = sensorData.location;
            const channel = sensorData.channel;
            
            // Get measurement data
            const temperature = sensorData.temperature;
            const correctedTemperature = sensorData.corrected_temperature;
            const humidity = sensorData.humidity;
            const correctedHumidity = sensorData.corrected_humidity;
            const date = sensorData.date;

            // Retrieve limits
            const thermoInfo = sensorData.thermo_info;
            const minTemperature = thermoInfo.min_temperature ?? -Infinity;
            const maxTemperature = thermoInfo.max_temperature ?? Infinity;
            const minHumidity = thermoInfo.min_humidity ?? -Infinity;
            const maxHumidity = thermoInfo.max_humidity ?? Infinity;

            // Get styles based on limits
            const getStyle = (value, min, max) => (value < min || value > max) ? 'color: red;' : 'color: black;';
            const temperatureStyle = getStyle(temperature, minTemperature, maxTemperature);
            const correctedTemperatureStyle = getStyle(correctedTemperature, minTemperature, maxTemperature);
            const humidityStyle = getStyle(humidity, minHumidity, maxHumidity);
            const correctedHumidityStyle = getStyle(correctedHumidity, minHumidity, maxHumidity);

            // Check if we already have a container for this sensor
            let sensorDiv = document.getElementById(`sensor-${sensorId}`);
            if (!sensorDiv) {
                sensorDiv = document.createElement('div');
                sensorDiv.id = `sensor-${sensorId}`;
                sensorDiv.className = 'sensor-data';
                
                const sensorHeader = document.createElement('h4');
                sensorHeader.textContent = `${sensorName} - ${location} (Channel ${channel})`;
                sensorDiv.appendChild(sensorHeader);
                
                sensorsContainer.appendChild(sensorDiv);
            }

            let formattedData = `
                <table>
                    <tr>
                        <th></th>
                        <th>Non Corrected</th>
                        <th>Corrected</th>
                    </tr>
                    <tr>
                        <td><strong>Temperature</strong></td>
                        <td style="${temperatureStyle}">${temperature} °C</td>
                        <td style="${correctedTemperatureStyle}">${correctedTemperature} °C</td>
                    </tr>
                    <tr>
                        <td><strong>Humidity</strong></td>
                        <td style="${humidityStyle}">${humidity} %</td>
                        <td style="${correctedHumidityStyle}">${correctedHumidity} %</td>
                    </tr>
                </table>
            `;

            if (date) {
                formattedData += `<p><strong>Instrument Date:</strong> ${date}</p>`;
            }

            // Update the sensor content (keeping its header)
            const sensorContent = sensorDiv.querySelector('.sensor-content');
            if (sensorContent) {
                sensorContent.innerHTML = formattedData;
            } else {
                const contentDiv = document.createElement('div');
                contentDiv.className = 'sensor-content';
                contentDiv.innerHTML = formattedData;
                sensorDiv.appendChild(contentDiv);
            }
        };

        ws.onerror = function (error) {
            console.error(`WebSocket error for ${selectedInstrumentName}:`, error);
            handleReconnection();
        };

        ws.onclose = function () {
            console.log(`WebSocket connection closed for ${selectedInstrumentName}`);
            handleReconnection();
        };
    }

    function handleReconnection() {
        resultDiv.querySelectorAll('.reconnect-message').forEach(msg => msg.remove());

        const reconnectMessage = document.createElement('p');
        reconnectMessage.className = 'reconnect-message';
        reconnectMessage.textContent = `Reconnecting to ${thermoName}... (Attempt ${reconnectAttempts + 1} of ${MAX_RECONNECT_ATTEMPTS})`;
        resultDiv.appendChild(reconnectMessage);

        delete thermohygrometerConnections[selectedThermohygrometer];
        reconnectAttempts += 1;

        if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) {
            setTimeout(createWebSocket, RECONNECT_DELAY);
        } else {
            resultDiv.querySelectorAll('.reconnect-message').forEach(msg => msg.remove());

            if (!resultDiv.querySelector('.failure-message')) {
                const failureMessage = document.createElement('p');
                failureMessage.className = 'failure-message';
                failureMessage.textContent = `Failed to reconnect to ${thermoName} after ${MAX_RECONNECT_ATTEMPTS} attempts. Please check the instrument and try again.`;
                resultDiv.appendChild(failureMessage);

                const removeButton = document.createElement('button');
                removeButton.textContent = 'Remove Instrument';
                removeButton.onclick = () => removeInstrument(selectedThermohygrometer);
                resultDiv.appendChild(removeButton);
            }
        }
    }

    createWebSocket();
}

function closeConnection(id) {
    const connection = thermohygrometerConnections[id];
    if (connection) {
        if (connection.readyState === WebSocket.OPEN) {
            connection.send(JSON.stringify({ command: 'disconnect' }));
        }
        connection.onclose = () => {
            console.log(`WebSocket connection closed for instrument with id: ${id}`);
            removeResultDiv(id);
        };
        connection.close();
    } else {
        console.log(`No active WebSocket connection found for instrument with id: ${id}`);
        removeResultDiv(id);
    }
}

function removeResultDiv(id) {
    const resultDiv = document.getElementById(`result-${id}`);
    if (resultDiv) {
        resultDiv.remove();
    } else {
        console.log(`No result div found for instrument with id: ${id}`);
    }
    delete thermohygrometerConnections[id];
}

function removeInstrument(id) {
    removeResultDiv(id);
}
