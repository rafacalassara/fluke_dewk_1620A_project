let ws = null;

document.addEventListener('DOMContentLoaded', async function() {
    try {
        const response = await fetch('/get_thermohygrometers/');
        const thermohygrometers = await response.json();
        const dropdown = document.getElementById('thermohygrometer');
        thermohygrometers.forEach(thermo => {
            const option = document.createElement('option');
            option.value = thermo.id;
            option.textContent = `${thermo.instrument_name} (PN: ${thermo.pn}, SN: ${thermo.sn})`;
            dropdown.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching thermohygrometers:', error);
    }
});

async function fetchRealTimeData() {
    const selectedThermohygrometer = document.getElementById('thermohygrometer').value;
    document.getElementById('result').textContent = 'Fetching data...';

    if (ws) {
        ws.close();
    }

    try {
        ws = new WebSocket(`ws://${window.location.host}/ws/data/${selectedThermohygrometer}/`);

        ws.onopen = function() {
            console.log('WebSocket connection opened');
            document.getElementById('close-button').style.display = 'inline-block';
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.error) {
                document.getElementById('result').textContent = 'Error: ' + data.error;
            } else {
                let formattedData = `
                    <p><strong>Temperature:</strong> ${data.data.temperature} °C</p>
                    <p><strong>Humidity:</strong> ${data.data.humidity} %</p>
                `;
                if (data.data.date) {
                    formattedData += `<p><strong>Date:</strong> ${data.data.date}</p>`;
                }
                document.getElementById('result').innerHTML = formattedData;
            }
        };

        ws.onerror = function(error) {
            document.getElementById('result').textContent = 'WebSocket error: ' + error.message;
        };

        ws.onclose = function() {
            console.log('WebSocket connection closed');
            document.getElementById('close-button').style.display = 'none';
        };
    } catch (error) {
        document.getElementById('result').textContent = 'Error fetching data: ' + error.message;
    }
}

function closeConnection() {
    if (ws) {
        ws.send(JSON.stringify({ command: 'disconnect' }));
        ws.close();
        document.getElementById('result').textContent = 'WebSocket connection closed';
        ws = null;
        document.getElementById('close-button').style.display = 'none';
    }
}
