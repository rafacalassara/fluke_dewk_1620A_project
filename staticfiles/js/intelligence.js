document.addEventListener('DOMContentLoaded', async function () {

    const form = document.querySelector('form')
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;


    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        const formData = new FormData(form);
        const data = {
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date'),
            start_time: formData.get('start_time'),
            end_time: formData.get('end_time'),
            instruments: Array.from(formData.getAll('instruments')).map(Number)
        };

        getChartData(data);
        getAnalysis(data);

    })

    let chartInstance = {};

    function showCharts({ data, analysis_period, humidity_data, temperature_data, total_time_available }) {

        document.querySelector('[data-analysis-period]').textContent = analysis_period
        document.querySelector('[data-time-available]').textContent = total_time_available
        document.querySelector("#results").style.display = 'block';

        const labels = data.map(item => item.instrument_name);
        const values = data.map(item => item.percent_out_of_limits);


        chartInstance.ctxBar?.destroy();
        chartInstance.temperatureCtx?.destroy();
        chartInstance.humidityCtx?.destroy();


        const ctxBar = document.getElementById('outOfLimitsChart').getContext('2d');
        chartInstance.ctxBar = new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: `Percentual fora dos limites (%) - Período: ${analysis_period}`,
                    data: values,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });

        // Gráfico de Temperatura
        const temperatureCtx = document.getElementById('temperatureChart').getContext('2d');
        const temperatureDatasets = Object.keys(temperature_data).map(instrument => ({
            label: instrument,
            data: temperature_data[instrument].map(entry => ({
                x: entry.timestamp,
                y: entry.value
            })),
            borderColor: getRandomColor(),
            fill: false,
            pointRadius: 0.5,
            spanGaps: true,
        }));

        chartInstance.temperatureCtx = new Chart(temperatureCtx, {
            type: 'line',
            data: {
                datasets: temperatureDatasets
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: { unit: 'hour' }
                    },
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

        // Gráfico de Umidade
        const humidityCtx = document.getElementById('humidityChart').getContext('2d');
        const humidityDatasets = Object.keys(humidity_data).map(instrument => ({
            label: instrument,
            data: humidity_data[instrument].map(entry => ({
                x: entry.timestamp,
                y: entry.value
            })),
            borderColor: getRandomColor(),
            fill: false,
            pointRadius: 0.5,
            spanGaps: false,
        }));

        chartInstance.humidityCtx = new Chart(humidityCtx, {
            type: 'line',
            data: {
                datasets: humidityDatasets
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: { unit: 'hour' }
                    },
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

    }

    function getRandomColor() {
        return `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 1)`;
    }

    function populateCard(data) {
        document.getElementById('title').innerText = data.title;
        document.getElementById('summary').innerText = data.summary;
        document.getElementById('analytics').innerText = data.analytics;
        document.getElementById('suggestion').innerText = data.suggestion;
        document.getElementById('conclusion').innerText = data.conclusion;
    }

    async function getChartData(data) {
        try {
            const response = await fetch('/api/environmental-analysis/out_of_limits_chart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const responseData = await response.json();
                showCharts(responseData);
            } else {
                console.error('Erro ao enviar formulário:', response.statusText);
                alert('Houve um erro ao enviar o formulário.');
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            alert('Erro na requisição.');
        }
    }

    async function getAnalysis(data) {
        try {
            document.getElementById('skeletonCard').style.display = 'block';
            document.getElementById('dataCard').style.display = 'none';

            const response = await fetch('/api/environmental-analysis/analyze_with_ai/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                console.log('Response data:', result);
                populateCard(result);

                document.getElementById('dataCard').style.display = 'block';
                document.getElementById('skeletonCard').style.display = 'none';
            } else {
                console.error('Erro na requisição:', result);
                alert('Houve um erro ao enviar o formulário: ' + result.error);
            }

        } catch (error) {
            console.error('Erro ao buscar dados:', error);
            document.getElementById('skeletonCard').style.display = 'none';
            alert('Erro ao processar os dados: ' + error.message);
        }
    }

});
