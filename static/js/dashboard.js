let surveyData = { bus: 2, auto: 1, bicicleta: 1, caminata: 2 };
let timeData = { 'Huancayo': 45, 'Jauja': 30, 'Chupaca': 60, 'Sicaya': 25, 'Orcotuna': 20 };
let totalResponses = 6, webResponses = 4, chatbotResponses = 2;
let pieChart = null, barChart = null;

function createPieChart() {
    const ctx = document.getElementById('pieChart');
    if (!ctx) return;
    if (pieChart) pieChart.destroy();
    pieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Bus', 'Auto', 'Bicicleta', 'Caminata'],
            datasets: [{
                data: [surveyData.bus, surveyData.auto, surveyData.bicicleta, surveyData.caminata],
                backgroundColor: ['#3498db', '#e67e22', '#27ae60', '#e74c3c'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        },
                        usePointStyle: true
                    }
                }
            }
        }
    });
}

function createBarChart() {
    const ctx = document.getElementById('barChart');
    if (!ctx) return;
    if (barChart) barChart.destroy();
    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(timeData),
            datasets: [{
                label: 'Tiempo (min)',
                data: Object.values(timeData),
                backgroundColor: '#27ae60',
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

function updateCharts() {
    if (pieChart) {
        pieChart.data.datasets[0].data = [surveyData.bus, surveyData.auto, surveyData.bicicleta, surveyData.caminata];
        pieChart.update();
    }
    if (barChart) {
        barChart.data.labels = Object.keys(timeData);
        barChart.data.datasets[0].data = Object.values(timeData);
        barChart.update();
    }
}

function updateMetrics() {
    document.getElementById('totalParticipants').textContent = totalResponses;
    document.getElementById('webResponses').textContent = webResponses;
    document.getElementById('chatbotResponses').textContent = chatbotResponses;
    document.getElementById('participantsCount').textContent = `${totalResponses} Participantes`;
    const avgMinutes = Math.round(Object.values(timeData).reduce((a, b) => a + b, 0) / Object.values(timeData).length);
    document.getElementById('avgTime').textContent = `${avgMinutes} min`;
}

function addTableRow(data) {
    const tbody = document.getElementById('responsesTable');
    const row = document.createElement('tr');
    const now = new Date();
    const timestamp = now.toLocaleString('es-PE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    row.innerHTML = `
        <td>${data.name}</td>
        <td>${data.location}</td>
        <td><span class="status-badge badge-${data.transport}">${data.transport.charAt(0).toUpperCase() + data.transport.slice(1)}</span></td>
        <td>${data.time}</td>
        <td><span class="status-badge source-${data.source}">${data.source === 'web' ? 'Web' : 'Chatbot'}</span></td>
        <td>${timestamp}</td>
    `;
    tbody.insertBefore(row, tbody.firstChild);
}

function saveDataToLocalStorage() {
    const data = {
        surveyData,
        timeData,
        totalResponses,
        webResponses,
        chatbotResponses
    };
    localStorage.setItem('transportSurveyData', JSON.stringify(data));
}

function loadDataFromLocalStorage() {
    const saved = localStorage.getItem('transportSurveyData');
    if (saved) {
        const data = JSON.parse(saved);
        surveyData = data.surveyData;
        timeData = data.timeData;
        totalResponses = data.totalResponses;
        webResponses = data.webResponses;
        chatbotResponses = data.chatbotResponses;
        return true;
    }
    return false;
}

function submitSurvey() {
    const formData = new FormData(document.getElementById('transportSurvey'));
    const transport = formData.get('transport');
    const name = formData.get('studentName');
    const location = formData.get('studentLocation');
    const minutes = parseInt(formData.get('travelMinutes')) || 0;

    if (!transport) {
        alert('Debe seleccionar un medio de transporte');
        return;
    }
    if (!name.trim()) {
        alert('Debe ingresar un nombre');
        return;
    }
    if (!location) {
        alert('Debe seleccionar una ubicación');
        return;
    }
    if (minutes <= 0) {
        alert('Debe ingresar un tiempo válido en minutos');
        return;
    }

    surveyData[transport]++;
    timeData[location] = minutes;
    totalResponses++;
    webResponses++;
    addTableRow({
        name,
        location,
        transport,
        time: `${minutes} min`,
        source: 'web'
    });
    updateMetrics();
    updateCharts();
    saveDataToLocalStorage();

    const alertMsg = document.getElementById('successMessage');
    alertMsg.style.display = 'block';
    setTimeout(() => alertMsg.style.display = 'none', 3000);
    document.getElementById('transportSurvey').reset();
    document.querySelectorAll('.transport-option').forEach(opt => opt.classList.remove('selected'));
}

window.saveChatbotResponse = function(data) {
    console.log('Datos recibidos del chatbot:', data);
    const transportMap = {
        bus: 'bus',
        auto: 'auto',
        carro: 'auto',
        automóvil: 'auto',
        bicicleta: 'bicicleta',
        bici: 'bicicleta',
        caminata: 'caminata',
        caminar: 'caminata',
        'a pie': 'caminata'
    };
    const transport = transportMap[data.transporte?.toLowerCase()] || data.transporte?.toLowerCase();
    const travelTime = parseInt(data.tiempo_llegada) || 0;

    if (transport && surveyData.hasOwnProperty(transport)) {
        surveyData[transport]++;
        if (data.lugar && travelTime > 0) timeData[data.lugar] = travelTime;
        totalResponses++;
        chatbotResponses++;
        addTableRow({
            name: data.nombre1 || 'Usuario Chatbot',
            location: data.lugar || 'No especificado',
            transport,
            time: `${travelTime} min`,
            source: 'chatbot'
        });
        updateMetrics();
        updateCharts();
        saveDataToLocalStorage();
        console.log('✅ Datos guardados exitosamente');
    } else {
        console.error('❌ Error: Datos del chatbot no válidos:', data);
    }
};

document.addEventListener('DOMContentLoaded', function() {
    const hasData = loadDataFromLocalStorage();
    setTimeout(() => {
        createPieChart();
        createBarChart();
        updateMetrics();
        if (!hasData) {
            setTimeout(() => window.saveChatbotResponse({
                nombre1: "Luis Rutti",
                lugar: "Orcotuna",
                edad: "20",
                transporte: "bus",
                tiempo_llegada: "30"
            }), 1000);
        }
    }, 100);
});

document.getElementById('transportSurvey').addEventListener('submit', function(e) {
    e.preventDefault();
    submitSurvey();
});

document.querySelectorAll('.transport-option').forEach(option => {
    option.addEventListener('click', function() {
        this.querySelector('input[type="radio"]').checked = true;
        document.querySelectorAll('.transport-option').forEach(opt => opt.classList.remove('selected'));
        this.classList.add('selected');
    });
});