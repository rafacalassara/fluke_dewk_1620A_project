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

    // Hide the "no instruments" message when adding a new instrument
    const noInstrumentsMessage = document.getElementById('no-instruments-message');
    if (noInstrumentsMessage) {
        noInstrumentsMessage.style.display = 'none';
    }

    // Create connection card for sidebar
    const connectionsContainer = document.getElementById('connections-container');
    
    const connectionCard = document.createElement('div');
    connectionCard.id = `connection-card-${selectedThermohygrometer}`;
    connectionCard.className = 'connection-card';
    
    // Create header with name and status indicator
    const cardHeader = document.createElement('div');
    cardHeader.className = 'connection-card-header';
    
    const nameTextShort = selectedInstrumentName.split(' - ')[0]; // Just get the instrument name
    
    cardHeader.innerHTML = `
        <p class="connection-name" title="${selectedInstrumentName}">
            <span class="connection-status-indicator"></span>
            ${nameTextShort}
        </p>
    `;
    
    // Create connection message
    const connectionMessage = document.createElement('p');
    connectionMessage.className = 'connection-message';
    connectionMessage.textContent = 'Connecting...';
    
    // Create actions div with disconnect button
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'connection-card-actions';
    
    connectionCard.appendChild(cardHeader);
    connectionCard.appendChild(connectionMessage);
    connectionCard.appendChild(actionsDiv);
    
    // Add to connections container
    connectionsContainer.appendChild(connectionCard);

    let reconnectAttempts = 0;

    function createWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/data/${selectedThermohygrometer}/`);

        thermohygrometerConnections[selectedThermohygrometer] = ws;

        ws.onopen = function () {
            console.log(`WebSocket connection opened for ${selectedInstrumentName}`);
            
            // Update the connection card in sidebar
            const connectionCard = document.getElementById(`connection-card-${selectedThermohygrometer}`);
            if (connectionCard) {
                const statusIndicator = connectionCard.querySelector('.connection-status-indicator');
                statusIndicator.style.backgroundColor = '#28a745'; // Green for connected
                
                const connectionMessage = connectionCard.querySelector('.connection-message');
                connectionMessage.textContent = 'Connected';
                connectionMessage.style.color = '#28a745';
                
                // Add disconnect button to actions
                const actionsDiv = connectionCard.querySelector('.connection-card-actions');
                actionsDiv.innerHTML = `<button class="btn btn-sm btn-danger" onclick="closeConnection('${selectedThermohygrometer}')">Disconnect</button>`;
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
            
            // Get reference to the result container
            const resultContainer = document.getElementById('result-container');
            
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

            // Get instrument information
            const instrumentName = thermoInfo.instrument_name;
            const instrumentPN = thermoInfo.pn;
            const instrumentSN = thermoInfo.sn;

            // Get styles based on limits
            const getStyle = (value, min, max) => (value < min || value > max) ? 'color: red;' : 'color: black;';
            const temperatureStyle = getStyle(temperature, minTemperature, maxTemperature);
            const correctedTemperatureStyle = getStyle(correctedTemperature, minTemperature, maxTemperature);
            const humidityStyle = getStyle(humidity, minHumidity, maxHumidity);
            const correctedHumidityStyle = getStyle(correctedHumidity, minHumidity, maxHumidity);

            // Create or update sensor box
            let sensorBox = document.getElementById(`sensor-${sensorId}`);
            if (!sensorBox) {
                sensorBox = document.createElement('div');
                sensorBox.id = `sensor-${sensorId}`;
                sensorBox.className = 'sensor-box';
                sensorBox.dataset.thermohygrometerKey = selectedThermohygrometer;
                
                resultContainer.appendChild(sensorBox);
            }

            // Update sensor box content
            sensorBox.innerHTML = `
                <div class="sensor-header">
                    <h4>${sensorName} - ${location}</h4>
                    <span class="channel-badge">CH ${channel}</span>
                </div>
                <div class="sensor-content">
                    <table>
                        <tr>
                            <th>Measurement</th>
                            <th>Raw</th>
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
                    ${date ? `<p class="timestamp">Timestamp: ${date}</p>` : ''}
                </div>
                <div class="instrument-info">
                    <h5>${instrumentName}</h5>
                    <p>P/N: ${instrumentPN} | S/N: ${instrumentSN}</p>
                </div>
            `;
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
        const connectionCard = document.getElementById(`connection-card-${selectedThermohygrometer}`);
        if (connectionCard) {
            const statusIndicator = connectionCard.querySelector('.connection-status-indicator');
            if (statusIndicator) {
                statusIndicator.style.backgroundColor = '#dc3545'; // Red for disconnected
            }
            
            const connectionMessage = connectionCard.querySelector('.connection-message');
            if (connectionMessage) {
                connectionMessage.textContent = `Reconnecting... (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`;
                connectionMessage.style.color = '#dc3545';
            }
        }

        delete thermohygrometerConnections[selectedThermohygrometer];
        reconnectAttempts += 1;

        if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) {
            setTimeout(createWebSocket, RECONNECT_DELAY);
        } else {
            if (connectionCard) {
                connectionCard.classList.add('disconnected');
                
                const connectionMessage = connectionCard.querySelector('.connection-message');
                if (connectionMessage) {
                    connectionMessage.textContent = 'Connection failed';
                }
                
                const actionsDiv = connectionCard.querySelector('.connection-card-actions');
                if (actionsDiv) {
                    actionsDiv.innerHTML = `<button class="btn btn-sm btn-secondary" onclick="removeInstrument('${selectedThermohygrometer}')">Remove</button>`;
                }
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
        connection.onclose = null; // Prevent the normal onclose handler
        connection.close();
        console.log(`WebSocket connection closed for instrument with id: ${id}`);
    }
    
    // Update the connection card in sidebar
    const connectionCard = document.getElementById(`connection-card-${id}`);
    if (connectionCard) {
        connectionCard.classList.add('disconnected');
        
        const statusIndicator = connectionCard.querySelector('.connection-status-indicator');
        if (statusIndicator) {
            statusIndicator.style.backgroundColor = '#dc3545'; // Red for disconnected
        }
        
        const connectionMessage = connectionCard.querySelector('.connection-message');
        if (connectionMessage) {
            connectionMessage.textContent = 'Disconnected';
            connectionMessage.style.color = '#dc3545';
        }
        
        const actionsDiv = connectionCard.querySelector('.connection-card-actions');
        if (actionsDiv) {
            actionsDiv.innerHTML = `<button class="btn btn-sm btn-secondary" onclick="removeInstrument('${id}')">Remove</button>`;
        }
    }
    
    // Remove all sensor boxes associated with this thermohygrometer
    document.querySelectorAll(`.sensor-box[data-thermohygrometer-key="${id}"]`).forEach(box => {
        box.remove();
    });
    
    delete thermohygrometerConnections[id];
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
    // Remove the connection card from sidebar
    const connectionCard = document.getElementById(`connection-card-${id}`);
    if (connectionCard) {
        connectionCard.remove();
    }
    
    // Remove all sensor boxes associated with this thermohygrometer
    document.querySelectorAll(`.sensor-box[data-thermohygrometer-key="${id}"]`).forEach(box => {
        box.remove();
    });
    
    delete thermohygrometerConnections[id];

    // Check if there are no more instruments connected
    const connectionsContainer = document.getElementById('connections-container');
    if (connectionsContainer && !connectionsContainer.querySelector('.connection-card')) {
        // Show the "no instruments" message again
        const noInstrumentsMessage = document.getElementById('no-instruments-message');
        if (noInstrumentsMessage) {
            noInstrumentsMessage.style.display = 'block';
        } else {
            // If the message doesn't exist, create it
            const newMessage = document.createElement('div');
            newMessage.id = 'no-instruments-message';
            newMessage.className = 'no-instruments-message';
            newMessage.innerHTML = `
                <p>No instruments connected</p>
                <small>Connect an instrument using the form above</small>
            `;
            connectionsContainer.appendChild(newMessage);
        }
    }
}
