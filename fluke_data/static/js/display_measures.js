// static/js/display_measures.js

document.addEventListener('DOMContentLoaded', async function () {
    const measuresContainer = document.getElementById('measures-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    let sensorData = {}; // Store sensor data instead of DOM elements
    let webSockets = {}; // Track active WebSocket connections
    let dataReceived = false; // Track if we've received any data

    // Fetch the list of connected thermohygrometers
    try {
        const response = await fetch('/api/v1/thermohygrometers/connected/');
        const thermohygrometers = await response.json();
        console.log('Connected thermohygrometers:', thermohygrometers);
        
        if (thermohygrometers.length === 0) {
            hideLoadingSpinner();
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
        
        // Set a timeout to hide the spinner if we don't get data in a reasonable time
        setTimeout(function() {
            if (!dataReceived) {
                hideLoadingSpinner();
                if (Object.keys(sensorData).length === 0) {
                    measuresContainer.innerHTML = '<p>No data received from instruments. Please check connections.</p>';
                }
            }
        }, 10000); // 10 seconds timeout
        
    } catch (error) {
        console.error('Error fetching thermohygrometers:', error);
        hideLoadingSpinner();
        measuresContainer.innerHTML = '<p>Error loading connected instruments. Please try again later.</p>';
    }

    function hideLoadingSpinner() {
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
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

    function updateOrCreateSensorBox(receivedData) {
        // Mark that we've received data
        if (!dataReceived) {
            dataReceived = true;
            hideLoadingSpinner();
        }
        
        // Parse the data - handle both direct data and data.data structures
        const data = receivedData.data ? receivedData.data : receivedData;
        
        // Check if we have all the required data
        if (!data || !data.sensor_id || !data.channel) {
            console.error('Invalid sensor data received:', data);
            return;
        }
        
        const sensorId = data.sensor_id;
        const channel = data.channel;
        // Create a unique key for each sensor-channel combination
        const boxKey = `${sensorId}-ch${channel}`;
        
        // Store sensor data in the outer sensorData object
        sensorData[boxKey] = {
            sensorId,
            channel,
            sensorName: data.sensor_name || 'Unknown Sensor',
            location: data.location || 'Unknown Location',
            temperature: data.temperature,
            correctedTemperature: data.corrected_temperature,
            humidity: data.humidity,
            correctedHumidity: data.corrected_humidity,
            date: data.date,
            thermoInfo: data.thermo_info || {},
        };
        
        console.log(`Stored data for sensor ${boxKey}. Total sensors: ${Object.keys(sensorData).length}`);
        console.log('Current sensor data:', sensorData);
        
        // Re-render all sensors in alphabetical order
        renderAllSensors();
    }
    
    function renderAllSensors() {
        // Clear container
        measuresContainer.innerHTML = '';
        
        // Get all keys and log them for debugging
        const allKeys = Object.keys(sensorData);
        console.log(`Rendering sensors. Total keys: ${allKeys.length}`, allKeys);
        
        // Sort sensor data alphabetically by location
        const sortedSensorKeys = allKeys.sort((a, b) => {
            return sensorData[a].location.localeCompare(sensorData[b].location);
        });
        
        if (sortedSensorKeys.length === 0) {
            measuresContainer.innerHTML = '<p>No sensor data available.</p>';
            return;
        }
        
        // Create and append sensor boxes in sorted order
        sortedSensorKeys.forEach(boxKey => {
            const data = sensorData[boxKey];
            
            // Get measurement data
            const {
                sensorId,
                channel, 
                sensorName,
                location,
                temperature,
                correctedTemperature,
                humidity,
                correctedHumidity,
                date,
                thermoInfo
            } = data;

            // Retrieve limits from thermo_info
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
            
            // Create sensor box
            const sensorBox = document.createElement('div');
            sensorBox.id = `sensor-${boxKey}`;
            sensorBox.className = 'sensor-box';
            
            sensorBox.innerHTML = `
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
            
            // Add to measures container
            measuresContainer.appendChild(sensorBox);
        });
    }
});
