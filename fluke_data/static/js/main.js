// static/js/main.js
let thermohygrometerConnections = {};

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

    try {
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
            // resultDiv.removeChild(connectingMessage);
            resultDiv.innerHTML += `<p>Error connecting to ${thermoName}: ${error.message}</p>`;
            delete thermohygrometerConnections[selectedThermohygrometer];
        };

        ws.onclose = function() {
            console.log(`WebSocket connection closed for ${selectedInstrumentName}`);
            delete thermohygrometerConnections[selectedThermohygrometer];
            if (document.contains(resultDiv)) {
                resultContainer.removeChild(resultDiv);
            }
        };
    } catch (error) {
        console.error(`Error establishing WebSocket connection for ${selectedInstrumentName}:`, error);
        resultDiv.removeChild(connectingMessage);
        resultDiv.innerHTML += `<p>Error fetching data: ${error.message}</p>`;
        delete thermohygrometerConnections[selectedThermohygrometer];
    }
}

function closeConnection(id) {
    if (thermohygrometerConnections[id]) {
        thermohygrometerConnections[id].send(JSON.stringify({ command: 'disconnect' }));
        thermohygrometerConnections[id].onclose = function() {
            console.log(`WebSocket connection closed for instrument with id: ${id}`);
            const resultDiv = document.getElementById(`result-${id}`);
            if (resultDiv) {
                resultDiv.remove();
            }
            delete thermohygrometerConnections[id];
        };
        thermohygrometerConnections[id].close();
    }
}
