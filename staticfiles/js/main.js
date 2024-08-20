// static/js/main.js

let thermohygrometerConnections = {};
const RECONNECT_DELAY = 5000; // Time in milliseconds to wait before trying to reconnect
const MAX_RECONNECT_ATTEMPTS = 3; // Number of times to attempt reconnection

document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/get_thermohygrometers/');
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
    const thermoName = selectedInstrumentName.split(' - ')[0]; // Instrument Name
    const thermoPNSN = selectedInstrumentName.split(' - ')[1]; // PN and SN

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

    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 3;
    const RECONNECT_DELAY = 5000; // 5 seconds delay for reconnection attempts

    function createWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/data/${selectedThermohygrometer}/`);
        
        thermohygrometerConnections[selectedThermohygrometer] = ws;

        ws.onopen = function() {
            console.log(`WebSocket connection opened for ${selectedInstrumentName}`);
            resultDiv.removeChild(connectingMessage);
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.error) {
                resultDiv.innerHTML += `<p>Error: ${data.error}</p>`;
            } else if (!data.data || typeof data.data.temperature === 'undefined' || typeof data.data.humidity === 'undefined') {
                console.log(`Data missing for ${selectedInstrumentName}.`);
            } else {
                let formattedData = `
                    <p><strong>Temperature:</strong> ${data.data.temperature} °C</p>
                    <p><strong>Humidity:</strong> ${data.data.humidity} %</p>
                `;
                if (data.data.date) {
                    formattedData += `<p><strong>Instrument Date:</strong> ${data.data.date}</p>`;
                }
                formattedData += `<button onclick="closeConnection('${selectedThermohygrometer}')">Close Connection</button>`;

                resultDiv.innerHTML = resultHeader.outerHTML + resultSubHeader.outerHTML + formattedData;
            }
        };

        ws.onerror = function(error) {
            console.error(`WebSocket error for ${selectedInstrumentName}:`, error);
            handleReconnection();
        };

        ws.onclose = function() {
            console.log(`WebSocket connection closed for ${selectedInstrumentName}`);
            handleReconnection();
        };
    }

    function handleReconnection() {
        // Clear any existing reconnect messages
        resultDiv.querySelectorAll('.reconnect-message').forEach(msg => msg.remove());

        const reconnectMessage = document.createElement('p');
        reconnectMessage.className = 'reconnect-message';
        reconnectMessage.textContent = `Reconnecting to ${thermoName}... (Attempt ${reconnectAttempts + 1} of ${MAX_RECONNECT_ATTEMPTS})`;
        resultDiv.appendChild(reconnectMessage);

        delete thermohygrometerConnections[selectedThermohygrometer];
        reconnectAttempts += 1;

        if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) {
            setTimeout(createWebSocket, RECONNECT_DELAY); // Attempt to reconnect after a delay
        } else {
            // Clear any existing reconnect messages
            resultDiv.querySelectorAll('.reconnect-message').forEach(msg => msg.remove());

            // Check if the failure message and remove button are already present
            if (!resultDiv.querySelector('.failure-message')) {
                const failureMessage = document.createElement('p');
                failureMessage.className = 'failure-message';
                failureMessage.textContent = `Failed to reconnect to ${thermoName} after ${MAX_RECONNECT_ATTEMPTS} attempts. Please check the instrument and try again.`;
                resultDiv.appendChild(failureMessage);

                const removeButton = document.createElement('button');
                removeButton.textContent = 'Remove Instrument';
                removeButton.onclick = function() {
                    removeInstrument(selectedThermohygrometer);
                };
                resultDiv.appendChild(removeButton);
            }
        }
    }

    createWebSocket();
}

function closeConnection(id) {
    if (thermohygrometerConnections[id]) {
        // Ensure the WebSocket connection exists before sending the disconnect command
        if (thermohygrometerConnections[id].readyState === WebSocket.OPEN) {
            thermohygrometerConnections[id].send(JSON.stringify({ command: 'disconnect' }));
        }

        // Assign a function to handle the close event
        thermohygrometerConnections[id].onclose = function() {
            console.log(`WebSocket connection closed for instrument with id: ${id}`);
            removeResultDiv(id);
        };

        // Close the WebSocket connection
        thermohygrometerConnections[id].close();
    } else {
        // Handle the case where the WebSocket connection might not exist
        console.log(`No active WebSocket connection found for instrument with id: ${id}`);
        removeResultDiv(id);
    }
}

// Helper function to remove the result HTML
function removeResultDiv(id) {
    const resultDiv = document.getElementById(`result-${id}`);
    if (resultDiv) {
        resultDiv.remove();
    } else {
        console.log(`No result div found for instrument with id: ${id}`);
    }
    delete thermohygrometerConnections[id];
}

// Function to remove the instrument from the UI and delete the connection
function removeInstrument(id) {
    removeResultDiv(id);
}