document.addEventListener('DOMContentLoaded', async function () {

    const form = document.querySelector('form')
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Mapa de cores fixas para instrumentos
    const instrumentColorMap = {};

    // Paleta de cores predefinida para instrumentos
    const colorPalette = [
        '#FF6384', // vermelho rosado
        '#36A2EB', // azul
        '#FFCE56', // amarelo
        '#4BC0C0', // turquesa
        '#9966FF', // roxo
        '#FF9F40', // laranja
        '#2ECC71', // verde esmeralda
        '#E74C3C', // vermelho tomate
        '#3498DB', // azul dodger
        '#9B59B6', // ametista
        '#1ABC9C', // verde água
        '#F1C40F', // amarelo sol
        '#E67E22', // laranja cenoura
        '#34495E'  // azul midnight
    ];

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
        // getAnalysis(data);

    });

    // Obtém cor fixa para um instrumento
    function getInstrumentColor(instrument) {
        if (!instrumentColorMap[instrument]) {
            // Atribui a próxima cor da paleta, ou gera uma aleatória se acabarem as cores da paleta
            const colorIndex = Object.keys(instrumentColorMap).length % colorPalette.length;
            instrumentColorMap[instrument] = colorPalette[colorIndex];
        }
        return instrumentColorMap[instrument];
    }

    let chartInstance = {};

    function showCharts({ data, analysis_period, humidity_data, temperature_data, total_time_available, timestamps }) {

        document.querySelector('[data-analysis-period]').textContent = analysis_period
        document.querySelector('[data-time-available]').textContent = total_time_available
        document.querySelector("#results").style.display = 'block';

        const labels = data.map(item => item.instrument_name);
        const values = data.map(item => item.percent_out_of_limits);

        // Destruir gráficos existentes se houver
        if (chartInstance.barChart) {
            chartInstance.barChart.destroy();
        }
        if (chartInstance.temperatureChart) {
            chartInstance.temperatureChart.destroy();
        }
        if (chartInstance.humidityChart) {
            chartInstance.humidityChart.destroy();
        }

        // Configuração do gráfico de barras
        const barChartOptions = {
            chart: {
                type: 'bar',
                height: 350
            },
            series: [{
                name: 'Percentual fora dos limites',
                data: values
            }],
            xaxis: {
                categories: labels
            },
            yaxis: {
                labels: {
                    formatter: function (val) {
                        return val.toFixed(2) + '%';
                    }
                },
                min: 0
            },
            title: {
                text: `Percentual fora dos limites (%) - Período: ${analysis_period}`,
                align: 'center'
            },
            colors: ['#36a2eb'],
            plotOptions: {
                bar: {
                    borderRadius: 2,
                    dataLabels: {
                        position: 'top'
                    }
                }
            },
            dataLabels: {
                enabled: true,
                formatter: function (val) {
                    return val.toFixed(2) + '%';
                },
                offsetY: -20,
                style: {
                    fontSize: '12px',
                    colors: ["#304758"]
                }
            }
        };

        // Criando o gráfico de barras
        chartInstance.barChart = new ApexCharts(document.querySelector('#outOfLimitsChart'), barChartOptions);
        chartInstance.barChart.render();

        // Identificar quais timestamps realmente têm dados em qualquer instrumento
        const timestampsWithData = new Set();
        const allTimestamps = [];
        
        // Processar dados de temperatura para encontrar todos os timestamps com dados reais
        Object.keys(temperature_data).forEach(instrument => {
            temperature_data[instrument].forEach(entry => {
                if (entry.value !== null && !isNaN(entry.value)) {
                    timestampsWithData.add(entry.timestamp);
                }
                allTimestamps.push(entry.timestamp);
            });
        });
        
        // Processar dados de umidade para encontrar todos os timestamps com dados reais
        Object.keys(humidity_data).forEach(instrument => {
            humidity_data[instrument].forEach(entry => {
                if (entry.value !== null && !isNaN(entry.value)) {
                    timestampsWithData.add(entry.timestamp);
                }
                allTimestamps.push(entry.timestamp);
            });
        });
        
        // Ordenar todos os timestamps únicos com dados
        const sortedTimestamps = Array.from(timestampsWithData).sort();
        
        // Obter timestamps mínimo e máximo para os limites do eixo (se houver dados)
        const minTimestamp = sortedTimestamps.length > 0 ? 
            new Date(sortedTimestamps[0]).getTime() : null;
        const maxTimestamp = sortedTimestamps.length > 0 ? 
            new Date(sortedTimestamps[sortedTimestamps.length - 1]).getTime() : null;
        
        // Agrupar timestamps por dia para categorias do eixo x
        const dayGroups = {};
        sortedTimestamps.forEach(timestamp => {
            const date = timestamp.split(' ')[0];
            if (!dayGroups[date]) {
                dayGroups[date] = [];
            }
            dayGroups[date].push(timestamp);
        });

        // Configuração do gráfico de temperatura com novos limites de eixo
        const temperatureSeries = Object.keys(temperature_data).map(instrument => {
            const color = getInstrumentColor(instrument);
            return {
                name: instrument,
                data: temperature_data[instrument]
                    .filter(entry => timestampsWithData.has(entry.timestamp) || entry.value !== null)
                    .map(entry => ({
                        x: new Date(entry.timestamp).getTime(),
                        y: (entry.value === null || isNaN(entry.value)) ? null : entry.value
                    })),
                color: color
            };
        });

        const temperatureChartOptions = {
            chart: {
                type: 'line',
                height: 350,
                animations: {
                    enabled: false  // Desabilita animações para melhorar o desempenho
                },
                toolbar: {
                    show: true,
                    tools: {
                        download: true,
                        selection: true,
                        zoom: true,
                        zoomin: true,
                        zoomout: true,
                        pan: true,
                        reset: true
                    }
                },
                zoom: {
                    enabled: true
                }
            },
            series: temperatureSeries,
            colors: temperatureSeries.map(series => series.color),
            stroke: {
                curve: 'straight',
                width: 1.5,
                lineCap: 'butt'
            },
            markers: {
                size: 0,
                hover: {
                    size: 4
                }
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    datetimeUTC: false,
                    format: 'dd/MM HH:mm'
                },
                // Definir min/max para mostrar apenas períodos com dados
                min: minTimestamp,
                max: maxTimestamp,
                // Agrupar por dias úteis
                tickAmount: Object.keys(dayGroups).length,
                // Adicionar rótulos para cada dia útil
                categories: Object.keys(dayGroups).map(day => {
                    const date = new Date(day);
                    return date.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' });
                })
            },
            yaxis: {
                title: {
                    text: 'Temperatura (°C)'
                },
                decimalsInFloat: 1
            },
            tooltip: {
                shared: false,
                intersect: false,
                x: {
                    format: 'dd MMM yyyy HH:mm:ss'
                }
            },
            legend: {
                position: 'top'
            },
            // Definição explícita para não conectar nulos
            connectNulls: false,
            noData: {
                text: 'Sem dados disponíveis'
            }
        };

        // Criando o gráfico de temperatura
        chartInstance.temperatureChart = new ApexCharts(document.querySelector('#temperatureChart'), temperatureChartOptions);
        chartInstance.temperatureChart.render();

        // Configuração do gráfico de umidade com os mesmos limites de eixo
        const humiditySeries = Object.keys(humidity_data).map(instrument => {
            const color = getInstrumentColor(instrument);
            return {
                name: instrument,
                data: humidity_data[instrument]
                    .filter(entry => timestampsWithData.has(entry.timestamp) || entry.value !== null)
                    .map(entry => ({
                        x: new Date(entry.timestamp).getTime(),
                        y: (entry.value === null || isNaN(entry.value)) ? null : entry.value
                    })),
                color: color
            };
        });

        const humidityChartOptions = {
            chart: {
                type: 'line',
                height: 350,
                animations: {
                    enabled: false  // Desabilita animações para melhorar o desempenho
                },
                toolbar: {
                    show: true,
                    tools: {
                        download: true,
                        selection: true,
                        zoom: true,
                        zoomin: true,
                        zoomout: true,
                        pan: true,
                        reset: true
                    }
                }
            },
            series: humiditySeries,
            colors: humiditySeries.map(series => series.color),
            stroke: {
                curve: 'straight',
                width: 1.5,
                lineCap: 'butt'
            },
            markers: {
                size: 0,
                hover: {
                    size: 4
                }
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    datetimeUTC: false,
                    format: 'dd/MM HH:mm'
                },
                // Definir min/max para mostrar apenas períodos com dados
                min: minTimestamp,
                max: maxTimestamp,
                // Agrupar por dias úteis
                tickAmount: Object.keys(dayGroups).length,
                // Adicionar rótulos para cada dia útil
                categories: Object.keys(dayGroups).map(day => {
                    const date = new Date(day);
                    return date.toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' });
                })
            },
            yaxis: {
                title: {
                    text: 'Umidade (%)'
                },
                decimalsInFloat: 1
            },
            tooltip: {
                shared: false,
                intersect: false,
                x: {
                    format: 'dd MMM yyyy HH:mm:ss'
                }
            },
            legend: {
                position: 'top'
            },
            // Definição explícita para não conectar nulos
            connectNulls: false,
            noData: {
                text: 'Sem dados disponíveis'
            }
        };

        // Criando o gráfico de umidade
        chartInstance.humidityChart = new ApexCharts(document.querySelector('#humidityChart'), humidityChartOptions);
        chartInstance.humidityChart.render();
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
            const response = await fetch('/api/v1/environmental-analysis/out-of-limits-chart/', {
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

            const response = await fetch('/api/v1/environmental-analysis/analyze-with-ai/', {
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
