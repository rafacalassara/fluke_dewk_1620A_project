// static/js/display_measures.js

document.addEventListener('DOMContentLoaded', async function () {
    const measuresContainer = document.getElementById('measures-container');
    let sensorBoxes = {}; // Track created sensor boxes
    let webSockets = {}; // Track active WebSocket connections

    // Fetch the list of connected thermohygrometers
    try {
        const response = await fetch('/api/v1/thermohygrometers/connected/');
        const thermohygrometers = await response.json();
        console.log(thermohygrometers);
        if (thermohygrometers.length === 0) {
            measuresContainer.innerHTML = `
                <div class="no-instruments-message">
                    <p>No instruments connected</p>
                    <small>Connect an instrument on the main dashboard first</small>
                </div>
            `;
            return;
        }

        // For each thermohygrometer, fetch its sensors
        for (const thermo of thermohygrometers) {
            try {
                const sensorsResponse = await fetch(`/api/v1/thermohygrometers/${thermo.id}/sensors/`);
                const sensors = await sensorsResponse.json();

                // Connect directly to individual sensors
                sensors.forEach(sensor => {
                    connectSensorWebSocket(thermo.id, sensor.id);
                });
            } catch (error) {
                console.error(`Error fetching sensors for thermohygrometer ${thermo.id}:`, error);
            }
        }
    } catch (error) {
        console.error('Error fetching thermohygrometers:', error);
        measuresContainer.innerHTML = '<p>Error loading connected instruments. Please try again later.</p>';
    }

    function connectSensorWebSocket(thermoId, sensorId) {
        const wsKey = `thermo_${thermoId}_sensor_${sensorId}`;
        const wsUrl = `ws://${window.location.host}/ws/listener/${thermoId}/sensor/${sensorId}/`;
        
        if (webSockets[wsKey]) {
            if (webSockets[wsKey].readyState === WebSocket.OPEN) {
                return; // Already connected
            }
            webSockets[wsKey].close();
        }
        
        const ws = new WebSocket(wsUrl);
        webSockets[wsKey] = ws;
        
        ws.onopen = function() {
            console.log(`WebSocket connection opened for sensor ${sensorId} on thermo ${thermoId}`);
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
            console.log(`WebSocket connection closed for sensor ${sensorId} on thermo ${thermoId}`);
        };
        
        ws.onerror = function(error) {
            console.error(`WebSocket error for sensor ${sensorId} on thermo ${thermoId}:`, error);
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
                <h4>${sensorName} - ${location}</h4>
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
                <h5>${instrumentName}</h5>
                <p>P/N: ${instrumentPN} | S/N: ${instrumentSN}</p>
                <span class="channel-badge">CH ${channel}</span>
            </div>
        `;
    }
});
