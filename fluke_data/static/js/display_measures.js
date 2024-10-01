// static/js/display_measures.js

document.addEventListener('DOMContentLoaded', async function() {
    const measuresContainer = document.getElementById('measures-container');

    // Fetch the list of connected thermohygrometers
    try {
        const response = await fetch('/get_connected_thermohygrometers/');
        const thermohygrometers = await response.json();

        // Create a box and establish WebSocket connection for each thermohygrometer
        thermohygrometers.forEach(thermo => {
            createInstrumentBox(thermo.id, thermo.instrument_name, thermo.pn, thermo.sn);
            connectWebSocket(thermo.id);
        });
    } catch (error) {
        console.error('Error fetching thermohygrometers:', error);
    }

    function createInstrumentBox(id, instrument_name, pn, sn) {
        const box = document.createElement('div');
        box.id = `instrument-${id}`;
        box.className = 'result';
        box.innerHTML = `
            <h3>${instrument_name}</h3>
            <p><strong>PN: ${pn}, SN: ${sn}<\strong><\p>
            <div id="data-${id}">
                <p><strong>Temperature:</strong> Loading...</p>
                <p><strong>Humidity:</strong> Loading...</p>
            </div>
        `;
        measuresContainer.appendChild(box);
    }

    function connectWebSocket(thermohygrometerId) {
        const ws = new WebSocket(`ws://${window.location.host}/ws/listener/${thermohygrometerId}/`);

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const dataContainer = document.getElementById(`data-${thermohygrometerId}`);
            if (data.date && data.temperature && data.humidity) {
                dataContainer.innerHTML = `
                    <table>
                        <tr>
                            <th></th>
                            <th>Non Corrected</th>
                            <th>Corrected</th>
                        </tr>
                        <tr>
                            <td><strong>Temperature</strong></td>
                            <td style="color: ${data.temperature_style};">${data.temperature} °C</td>
                            <td style="color: ${data.corrected_temperature_style};">${data.corrected_temperature} °C</td>
                        </tr>
                        <tr>
                            <td><strong>Humidity</strong></td>
                            <td style="color: ${data.humidity_style};">${data.humidity} %</td>
                            <td style="color: ${data.corrected_humidity_style};">${data.corrected_humidity} %</td>
                        </tr>
                    </table>
                    ${data.date ? `<p><strong>Instrument Date:</strong> ${data.date}</p>` : ''}
                `;
            } else {
                dataContainer.innerHTML = '<p>No valid data received.</p>';
            }
        };

        ws.onclose = function() {
            console.log(`WebSocket connection closed for instrument ID: ${thermohygrometerId}`);
        };
    }
});
