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
    
    // Create header container with flex layout
    const headerContainer = document.createElement('div');
    headerContainer.className = 'instrument-header';
    
    // Add the header text
    const resultHeader = document.createElement('h3');
    resultHeader.textContent = thermoName;
    headerContainer.appendChild(resultHeader);
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.className = 'close-button';
    closeButton.innerHTML = '&times;'; // × symbol
    closeButton.title = 'Disconnect instrument';
    closeButton.onclick = () => closeConnection(selectedThermohygrometer);
    headerContainer.appendChild(closeButton);
    
    // Add the header container to result div
    resultDiv.appendChild(headerContainer);

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
                sensorDiv.className = 'sensor-box';
                
                const sensorHeader = document.createElement('div');
                sensorHeader.className = 'sensor-header';
                
                const sensorTitle = document.createElement('h4');
                sensorTitle.textContent = `${sensorName} - ${location}`;
                sensorHeader.appendChild(sensorTitle);
                
                const channelBadge = document.createElement('span');
                channelBadge.className = 'channel-badge';
                channelBadge.textContent = `CH ${channel}`;
                sensorHeader.appendChild(channelBadge);
                
                sensorDiv.appendChild(sensorHeader);
                
                sensorsContainer.appendChild(sensorDiv);
                
                // Add CSS to make the sensor boxes look good
                const style = document.createElement('style');
                if (!document.getElementById('sensor-box-styles')) {
                    style.id = 'sensor-box-styles';
                    style.textContent = '/* Styles merged with instrument-styles */';
                    document.head.appendChild(style);
                }
            }

            let formattedData = `
                <table>
                    <tr>
                        <th>Measurement</th>
                        <th>Non Corrected</th>
                        <th>Corrected</th>
                    </tr>
                    <tr>
                        <td>Temperature</td>
                        <td style="${temperatureStyle}">${temperature} °C</td>
                        <td style="${correctedTemperatureStyle}">${correctedTemperature} °C</td>
                    </tr>
                    <tr>
                        <td>Humidity</td>
                        <td style="${humidityStyle}">${humidity} %</td>
                        <td style="${correctedHumidityStyle}">${correctedHumidity} %</td>
                    </tr>
                </table>
            `;

            if (date) {
                formattedData += `<p class="timestamp">Instrument Date: ${date}</p>`;
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

    // Add CSS for the instrument header and close button
    const style = document.createElement('style');
    if (!document.getElementById('instrument-styles')) {
        style.id = 'instrument-styles';
        style.textContent = `
            .result {
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid #ddd;
            }
            .instrument-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 2px solid #eaeaea;
            }
            .instrument-header h3 {
                margin: 0;
                font-size: 1.5em;
                color: #2c3e50;
            }
            .close-button {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                font-size: 20px;
                line-height: 0;
                cursor: pointer;
                display: flex;
                justify-content: center;
                align-items: center;
                transition: all 0.2s;
            }
            .close-button:hover {
                background-color: #c0392b;
                transform: scale(1.1);
            }
            .sensors-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 15px;
            }
            .sensor-box {
                flex: 1 0 300px;
                min-width: 300px;
                max-width: 450px;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 15px;
                background-color: #f9f9f9;
                transition: transform 0.2s;
            }
            .sensor-box:hover {
                transform: translateY(-3px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .sensor-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #eee;
                padding-bottom: 8px;
                margin-bottom: 10px;
            }
            .sensor-header h4 {
                margin: 0;
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
            .channel-badge {
                background-color: #3498db;
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .sensor-content table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }
            .sensor-content th, .sensor-content td {
                padding: 10px;
                border-bottom: 1px solid #eee;
                text-align: left;
            }
            .sensor-content th {
                background-color: #f2f2f2;
                font-weight: 600;
                color: #555;
            }
            .sensor-content td:first-child {
                text-align: left;
                font-weight: bold;
                width: 30%;
            }
            .sensor-content td:nth-child(2), .sensor-content td:nth-child(3) {
                text-align: right;
                width: 35%;
            }
            .timestamp {
                font-size: 0.9em;
                color: #777;
                text-align: right;
                margin-top: 10px;
                margin-bottom: 0;
                font-style: italic;
            }
            .reconnect-message, .failure-message {
                color: #e74c3c;
                margin: 10px 0;
                padding: 8px;
                background-color: #fadbd8;
                border-radius: 4px;
                border-left: 4px solid #e74c3c;
            }
            .failure-message {
                margin-bottom: 15px;
            }
            .failure-message + button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                transition: background-color 0.2s;
            }
            .failure-message + button:hover {
                background-color: #2980b9;
            }
        `;
        document.head.appendChild(style);
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
