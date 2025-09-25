// ==============================
// app.js
// ==============================

// Tipo de gráfico actual (cambiable)
let currentChartType = "pie";

// -----------------------------
// Función para obtener datos del backend
// -----------------------------
async function fetchData(filters = {}) {
    const res = await axios.get(`/api/data?${new URLSearchParams(filters)}`);
    return res.data;
}

// -----------------------------
// Rellenar <select> dinámicamente
// -----------------------------
function fillOptions(selectId, values) {
    const sel = document.getElementById(selectId);
    const current = sel.value;
    sel.innerHTML = `<option value="">Todas</option>`;
    values.forEach(v => sel.innerHTML += `<option value="${v}">${v}</option>`);
    sel.value = current;
}

// -----------------------------
// Obtener filtros activos
// -----------------------------
function getFilters() {
    return {
        escuela: document.getElementById("filterEscuela").value,
        fecha: document.getElementById("filterFecha").value,
        transporte: document.getElementById("filterTransporte").value
    };
}

// -----------------------------
// Refrescar datos y gráficos
// -----------------------------
async function refresh(filters = {}, showCharts = true) {
    try {
        const { total, counts, escuelas, fechas, registros } = await fetchData(filters);

        // Métricas
        document.getElementById("total-participantes").textContent = total;
        document.getElementById("respuestas-web").textContent = registros.filter(r => r.origen && r.origen.toLowerCase() === 'web').length;
        document.getElementById("respuestas-chatbot").textContent = registros.filter(r => r.origen && r.origen.toLowerCase() === 'chatbot').length;

        // Filtros dinámicos
        fillOptions("filterEscuela", escuelas);
        fillOptions("filterFecha", fechas);

        // Tabla
        const tbody = document.getElementById("tabla-respuestas");
        tbody.innerHTML = "";
        registros.forEach(r => {
            tbody.innerHTML += `<tr>
                <td>${r.id || '-'}</td>
                <td>${r.nombre || ''} ${r.apellido || ""}</td>
                <td>${r.escuela || '-'}</td>
                <td>${r.transporte || '-'}</td>
                <td>${r.distrito || "-"}</td>
                <td>${r.tiempo_encuesta || '-'}</td>
            </tr>`;
        });

        // Actualizar enlace de descarga
        const downloadLink = document.getElementById("downloadCsv");
        const filterParams = new URLSearchParams();
        Object.keys(filters).forEach(key => {
            if (filters[key]) filterParams.append(key, filters[key]);
        });
        downloadLink.href = `/api/export?${filterParams.toString()}`;

        // Gráficos
        if (showCharts) {
            updateCharts(filters);
        }
    } catch (err) {
        console.error("Error al refrescar datos:", err);
    }
}

// -----------------------------
// Actualizar gráficos
// -----------------------------
function updateCharts(filters = {}) {
    const t = Date.now(); // evitar cache
    const filterParams = new URLSearchParams();
    
    // Solo agregar filtros que tengan valor
    Object.keys(filters).forEach(key => {
        if (filters[key] && filters[key].trim() !== '') {
            filterParams.append(key, filters[key]);
        }
    });
    
    console.log("Actualizando gráficos con filtros:", filters);
    console.log("Tipo de gráfico actual:", currentChartType);
    
    // Función para manejar errores de carga de imagen
    const handleImageError = (img, chartName) => {
        img.onerror = (error) => {
            console.error(`Error cargando ${chartName}:`, error);
            // Mostrar imagen de error más informativa
            img.src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIiBzdHJva2U9IiNkZWUyZTYiIHN0cm9rZS13aWR0aD0iMSIvPjx0ZXh0IHg9IjUwJSIgeT0iNDAlIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNkYzM1NDUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5FcnJvciBhbCBjYXJnYXI8L3RleHQ+PHRleHQgeD0iNTAlIiB5PSI2MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxMiIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkludGVudGUgcmVjYXJnYXIgbGEgcMOhZ2luYTwvdGV4dD48L3N2Zz4=";
        };
        img.onload = () => {
            console.log(`${chartName} cargado correctamente`);
        };
        
        // Timeout para detectar imágenes que no cargan
        setTimeout(() => {
            if (img.naturalWidth === 0) {
                console.warn(`${chartName} no se cargó después de 5 segundos`);
            }
        }, 5000);
    };
    
    // Gráfico filtrado (usa el tipo seleccionado)
    const img1 = document.getElementById("chartImage1");
    const url1 = `/api/chart/${currentChartType}.png?${filterParams.toString()}&t=${t}`;
    console.log("URL gráfico filtrado:", url1);
    img1.src = url1;
    handleImageError(img1, "Gráfico filtrado");
    
    // Gráfico general (usa el tipo seleccionado) 
    const img2 = document.getElementById("chartImage2");
    const url2 = `/api/chart/${currentChartType}.png?t=${t}`;
    console.log("URL gráfico general:", url2);
    img2.src = url2;
    handleImageError(img2, "Gráfico general");
    
    // Gráfico comparativo (siempre barras para comparar)
    const img3 = document.getElementById("chartImage3");
    const compareParams = new URLSearchParams();
    compareParams.append('compare', '1');
    Object.keys(filters).forEach(key => {
        if (filters[key] && filters[key].trim() !== '') {
            compareParams.append(key, filters[key]);
        }
    });
    compareParams.append('t', t);
    const url3 = `/api/chart/bar.png?${compareParams.toString()}`;
    console.log("URL gráfico comparativo:", url3);
    img3.src = url3;
    handleImageError(img3, "Gráfico comparativo");
}

// -----------------------------
// Cambiar tipo de gráfico
// -----------------------------
function setupChartTypeButtons() {
    const chartButtons = document.querySelectorAll('.btn-chart');
    
    chartButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remover clase activa de todos los botones
            chartButtons.forEach(b => b.classList.remove('active'));
            
            // Agregar clase activa al botón clickeado
            btn.classList.add('active');
            
            // Actualizar tipo de gráfico
            currentChartType = btn.dataset.type;
            
            // Actualizar gráficos
            updateCharts(getFilters());
        });
    });
    
    // Activar botón por defecto
    document.querySelector('.btn-chart[data-type="pie"]').classList.add('active');
}

// -----------------------------
// Enviar nueva respuesta
// -----------------------------
function setupForm() {
    document.getElementById("encuestaForm").addEventListener("submit", async e => {
        e.preventDefault();
        const form = e.target;
        const data = {
            nombre: form.nombre.value.trim(),
            apellido: form.apellido.value.trim(),
            escuela: form.escuela.value.trim(),
            transporte: form.transporte.value,
            comentario: form.comentario.value.trim(),
            origen: "Web"
        };
        
        if (!data.nombre || !data.transporte) {
            alert("Por favor complete los campos requeridos");
            return;
        }
        
        try {
            await axios.post("/api/submit", data);
            form.reset();
            await refresh(getFilters(), true);
            alert("Respuesta enviada correctamente");
        } catch (err) {
            console.error("Error al enviar respuesta:", err);
            alert("Error al enviar la encuesta");
        }
    });
}

// -----------------------------
// Aplicar filtros
// -----------------------------
function setupFilters() {
    document.getElementById("applyFilters").addEventListener("click", async () => {
        console.log("Aplicando filtros...");
        const filters = getFilters();
        console.log("Filtros aplicados:", filters);
        
        // Limpiar las imágenes primero para mostrar que están recargando
        const images = ['chartImage1', 'chartImage2', 'chartImage3'];
        images.forEach(id => {
            const img = document.getElementById(id);
            img.src = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjhmOWZhIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzZjNzU3ZCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkNhcmdhbmRvLi4uPC90ZXh0Pjwvc3ZnPg==";
        });
        
        await refresh(filters, true);
    });
    
    // Botón para limpiar filtros
    document.getElementById("clearFilters").addEventListener("click", async () => {
        console.log("Limpiando filtros...");
        document.getElementById("filterEscuela").value = "";
        document.getElementById("filterFecha").value = "";
        document.getElementById("filterTransporte").value = "";
        await refresh({}, true);
    });
    
    // Botón para recargar gráficos
    document.getElementById("refreshCharts").addEventListener("click", async () => {
        console.log("Recargando gráficos...");
        const filters = getFilters();
        updateCharts(filters);
    });
}

// -----------------------------
// Inicialización al cargar la página
// -----------------------------
window.addEventListener("load", async () => {
    console.log("Iniciando aplicación...");
    
    try {
        // Configurar event listeners
        setupForm();
        setupFilters();
        setupChartTypeButtons();
        
        console.log("Event listeners configurados");
        
        // Cargar datos iniciales
        console.log("Cargando datos iniciales...");
        await refresh({}, true);
        
        console.log("Aplicación inicializada correctamente");
        
        // Verificar que las imágenes se están cargando
        setTimeout(() => {
            const imgs = document.querySelectorAll('.chart-card img');
            imgs.forEach((img, index) => {
                if (!img.src || img.src === window.location.href) {
                    console.warn(`Imagen ${index + 1} no tiene src válido`);
                } else {
                    console.log(`Imagen ${index + 1} src:`, img.src);
                }
            });
        }, 1000);
        
    } catch (err) {
        console.error("Error al inicializar la aplicación:", err);
        alert("Error al inicializar la aplicación. Revise la consola para más detalles.");
    }
});