// static/js/display_measures.js

document.addEventListener('DOMContentLoaded', async function () {
    const measuresContainer = document.getElementById('measures-container');
    let sensorBoxes = {}; // Track created sensor boxes
    let webSockets = {}; // Track active WebSocket connections

    // Fetch the list of connected thermohygrometers
    try {
        const response = await fetch('/api/v1/thermohygrometers/connected/');
        const thermohygrometers = await response.json();
        console.log('Connected thermohygrometers:', thermohygrometers);
        
        if (thermohygrometers.length === 0) {
            measuresContainer.innerHTML = `
                <div class="no-instruments-message">
                    <p>No instruments connected</p>
                    <small>Connect an instrument on the main dashboard first</small>
                </div>
            `;
            return;
        }

        // For each thermohygrometer, connect to WebSocket
        for (const thermo of thermohygrometers) {
            try {
                // Instead of fetching sensors via API, connect directly to thermohygrometer WebSocket
                connectThermoWebSocket(thermo.id);
            } catch (error) {
                console.error(`Error connecting to thermohygrometer ${thermo.id}:`, error);
            }
        }
    } catch (error) {
        console.error('Error fetching thermohygrometers:', error);
        measuresContainer.innerHTML = '<p>Error loading connected instruments. Please try again later.</p>';
    }

    function connectThermoWebSocket(thermoId) {
        const wsKey = `thermo_${thermoId}`;
        const wsUrl = `ws://${window.location.host}/ws/listener/${thermoId}/`;
        
        if (webSockets[wsKey]) {
            if (webSockets[wsKey].readyState === WebSocket.OPEN) {
                return; // Already connected
            }
            webSockets[wsKey].close();
        }
        
        console.log(`Connecting to thermohygrometer WebSocket: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);
        webSockets[wsKey] = ws;
        
        ws.onopen = function() {
            console.log(`WebSocket connection opened for thermohygrometer ${thermoId}`);
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.error) {
                console.error(`WebSocket error: ${data.error}`);
                return;
            }
            updateOrCreateSensorBox(data);
        };
        
        ws.onclose = function() {
            console.log(`WebSocket connection closed for thermohygrometer ${thermoId}`);
        };
        
        ws.onerror = function(error) {
            console.error(`WebSocket error for thermohygrometer ${thermoId}:`, error);
        };
    }

    function updateOrCreateSensorBox(sensorData) {
        // Parse the data - handle both direct data and data.data structures
        const data = sensorData.data ? sensorData.data : sensorData;
        
        // Check if we have all the required data
        if (!data || !data.sensor_id || !data.channel) {
            console.error('Invalid sensor data received:', data);
            return;
        }
        
        const sensorId = data.sensor_id;
        const channel = data.channel;
        // Create a unique key for each sensor-channel combination
        const boxKey = `${sensorId}-ch${channel}`;
        
        // Get sensor data
        const sensorName = data.sensor_name || 'Unknown Sensor';
        const location = data.location || 'Unknown Location';
        
        // Get measurement data
        const temperature = data.temperature;
        const correctedTemperature = data.corrected_temperature;
        const humidity = data.humidity;
        const correctedHumidity = data.corrected_humidity;
        const date = data.date;

        // Retrieve limits from thermo_info
        const thermoInfo = data.thermo_info || {};
        const minTemperature = thermoInfo.min_temperature ?? -Infinity;
        const maxTemperature = thermoInfo.max_temperature ?? Infinity;
        const minHumidity = thermoInfo.min_humidity ?? -Infinity;
        const maxHumidity = thermoInfo.max_humidity ?? Infinity;

        // Get instrument information
        const instrumentName = thermoInfo.instrument_name || 'Unknown Instrument';
        const instrumentPN = thermoInfo.pn || 'N/A';
        const instrumentSN = thermoInfo.sn || 'N/A';
        const instrumentLocation = thermoInfo.instrument_location || 'Unknown Location';

        // Get styles based on limits
        const getStyle = (value, min, max) => (value < min || value > max) ? 'color: red;' : 'color: black;';
        const temperatureStyle = getStyle(temperature, minTemperature, maxTemperature);
        const correctedTemperatureStyle = getStyle(correctedTemperature, minTemperature, maxTemperature);
        const humidityStyle = getStyle(humidity, minHumidity, maxHumidity);
        const correctedHumidityStyle = getStyle(correctedHumidity, minHumidity, maxHumidity);

        // Create or update sensor box using the combined key
        if (!sensorBoxes[boxKey]) {
            // Create new sensor box if it doesn't exist
            const sensorBox = document.createElement('div');
            sensorBox.id = `sensor-${boxKey}`;
            sensorBox.className = 'sensor-box';
            
            // Add to measures container and track it
            measuresContainer.appendChild(sensorBox);
            sensorBoxes[boxKey] = sensorBox;
        }

        // Update sensor box content
        sensorBoxes[boxKey].innerHTML = `
            <div class="sensor-header">
                <h4>${location}</h4>
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
                ${date ? `<p class="timestamp"><strong>Instrument Date: </strong>${date}</p>` : ''}
            </div>
            <div class="instrument-info">
                <h5>${instrumentName}  <span class="channel-badge">CH ${channel}</span></h5>
                <p>Termohigrometro na: ${instrumentLocation}</p>
                <p>P/N: ${instrumentPN} | S/N: ${instrumentSN}</p>
                
            </div>
        `;
    }
});
