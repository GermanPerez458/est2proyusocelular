const app = {
    sessionId: null,
    statsActuales: null,
    datosCrudos: null,

    init() {
        console.log('Requiem Engine 3.5.0 Inicializado');
        this.setupEventListeners();
        this.checkHealth();
    },

    setupEventListeners() {
        const csvFile = document.getElementById('csvFile');
        if (csvFile) {
            csvFile.addEventListener('change', (e) => {
                if (e.target.files.length > 0) this.uploadCSV();
            });
        }
        
        const btnPreview = document.getElementById('btnPreview');
        if (btnPreview) {
            btnPreview.addEventListener('click', () => this.togglePreview());
        }
    },

    // --- COMUNICACIÓN API ---
    
    async checkHealth() {
        try {
            await fetch('/api/analisis_rapido', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: 'ping'}) 
            });
            console.log('Backend disponible');
        } catch (e) {
            console.warn("Backend en espera de sesión...");
        }
    },

    async uploadCSV() {
        const fileInput = document.getElementById('csvFile');
        if (!fileInput.files.length) return;

        const fd = new FormData();
        fd.append('file', fileInput.files[0]);
        this.toggleLoading(true);

        try {
            const r = await fetch('/api/upload', { method: 'POST', body: fd });
            const d = await r.json();
            
            if (r.ok && d.session_id) {
                this.sessionId = d.session_id;
                this.statsActuales = d.estadisticas;
                this.datosCrudos = d.datos || d.filas || [];
                
                this.enableAnalysisButton();
                this.notify(`✓ Datos cargados: ${this.datosCrudos.length} registros válidos`, 'success');
                this.mostrarVistaPrevia(d.estadisticas, 'vista-previa');
            } else {
                this.notify(d.error || 'Error al procesar el archivo CSV', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.notify('Error de conexión con el servidor', 'error');
        } finally {
            this.toggleLoading(false);
            fileInput.value = '';
        }
    },

    async generarEjemplo() {
        // 1. Captura y validación de inputs
        const n = parseInt(document.getElementById('nEjemplo')?.value) || 100;
        const media = parseFloat(document.getElementById('mediaEjemplo')?.value) || 5.5;
        const desviacion = parseFloat(document.getElementById('desvEjemplo')?.value) || 1.5;

        if (n < 3 || n > 10000) {
            return this.notify('El tamaño de muestra debe estar entre 3 y 10000', 'error');
        }

        const payload = { n, media, desviacion };

        // 2. Preparación de UI
        this.toggleLoading(true);
        
        const previewPanel = document.getElementById("previewDatos");
        if (previewPanel) previewPanel.classList.add("hidden");

        try {
            const r = await fetch('/api/generar_ejemplo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const d = await r.json();
            
            if (r.ok && d.success) {
                // 3. Sincronización de estado global
                this.sessionId = d.session_id;
                this.statsActuales = d.estadisticas;
                this.datosCrudos = d.datos || d.filas || []; 
                
                // 4. Actualización de Interfaz
                this.enableAnalysisButton();
                this.notify(`✓ Simulación Gamma generada: ${this.datosCrudos.length} observaciones`, 'success');
                this.mostrarVistaPrevia(d.estadisticas, 'vista-previa');
                
            } else {
                this.notify(d.error || 'Error en los parámetros de simulación', 'error');
            }
        } catch (error) {
            console.error("Fetch Error:", error);
            this.notify('Error crítico: No se pudo conectar con el motor estadístico', 'error');
        } finally {
            this.toggleLoading(false);
        }
    },
    
    async ejecutarAnalisis() {
        // 1. Validación preventiva
        if (!this.sessionId) {
            return this.notify('Error: No se detectó una sesión activa. Reintente cargar los datos.', 'error');
        }

        const contenedor = document.getElementById('contenedor-analisis');
        const umbralEl = document.getElementById('input-umbral');
        const confianzaEl = document.getElementById('nivel-confianza');

        if (!contenedor) {
            console.error("Error: Contenedor de análisis no encontrado en el DOM");
            return;
        }

        // 2. Recolección de parámetros
        const params = {
            session_id: this.sessionId,
            umbral: parseFloat(umbralEl?.value) || 5.0,
            nivel_confianza: parseFloat(confianzaEl?.value) || 0.95
        };

        // 3. Preparación de UI
        this.toggleLoading(true);
        contenedor.innerHTML = `<div class="text-center py-20 animate-pulse text-elephant-400 font-mono uppercase tracking-widest text-xs">
            Procesando motores de inferencia...
        </div>`;

        try {
            const r = await fetch('/api/analisis_completo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });

            const data = await r.json();

            if (r.ok) {
                contenedor.innerHTML = ''; 
                const capKeys = [
                    'capitulo1_descriptiva', 
                    'capitulo2_estimacion', 
                    'capitulo3_intervalos', 
                    'capitulo4_hipotesis', 
                    'capitulo5_comparacion'
                ];
                
                let currentBatch = 0;

                const renderBatch = () => {
                    if (currentBatch < capKeys.length) {
                        const key = capKeys[currentBatch];
                        if (data[key] && !data[key].error) {
                            this.renderCapitulo(data[key], currentBatch);
                        } else if (data[key] && data[key].error) {
                            console.warn(`Error en ${key}:`, data[key].error);
                        }
                        currentBatch++;
                        requestAnimationFrame(() => setTimeout(renderBatch, 60));
                    } else {
                        this.triggerMathJax(contenedor);
                        this.toggleLoading(false);
                        this.notify('✓ Análisis inferencial completado', 'success');
                        
                        // Scroll suave al contenedor de resultados
                        contenedor.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                };
                
                renderBatch();

            } else {
                throw new Error(data.error || 'Error desconocido en el servidor');
            }
        } catch (error) {
            console.error("Fallo Crítico:", error);
            this.notify(error.message || 'Fallo en la conexión con el servidor', 'error');
            this.toggleLoading(false);
            contenedor.innerHTML = `
                <div class="text-center py-20 opacity-20 border-2 border-dashed border-elephant-700 rounded-2xl">
                    <p class="font-mono text-sm tracking-widest uppercase">Error en el flujo de datos. Reintente el análisis.</p>
                </div>`;
        }
    },

    // --- MOTOR MATEMÁTICO ---

    triggerMathJax(element) {
        if (window.MathJax && window.MathJax.typesetPromise) {
            console.log("Iniciando motor MathJax...");
            setTimeout(() => {
                MathJax.typesetPromise([element])
                    .then(() => console.log("✓ Fórmulas procesadas correctamente"))
                    .catch((err) => {
                        console.error("Fallo MathJax:", err);
                        if(window.MathJax.typeset) window.MathJax.typeset();
                    });
            }, 150); 
        } else {
            console.error("Librería MathJax no detectada en el sistema.");
        }
    },

    // --- RENDERIZADO UI ---

    renderCapitulo(cap, index) {
        const contenedor = document.getElementById('contenedor-analisis');
        const idGrafico = `grafico-cap-${index}`;
        
        const html = `
            <div class="glass-card p-8 mb-10 border-t-2 border-elephant-400 animate-fadeIn" style="animation: fadeIn 0.5s ease-in;">
                <div class="mb-4">
                    <span class="text-[10px] font-mono text-elephant-400 uppercase tracking-widest">Módulo Estadístico ${index + 1}</span>
                    <h2 class="text-2xl font-bold text-white">${cap.titulo || 'Análisis'}</h2>
                </div>
                <p class="text-elephant-300 mb-6 text-sm leading-relaxed">${cap.descripcion || ''}</p>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                        <h3 class="text-xs font-bold uppercase text-elephant-400 mb-3 tracking-wider">Desarrollo Matemático</h3>
                        <div class="desarrollo-pasos-container min-h-[100px] text-white">
                            ${cap.formulas?.latex || '<p class="text-elephant-500">Sin fórmulas disponibles</p>'}
                        </div>
                        
                        <h3 class="text-xs font-bold uppercase text-elephant-400 mt-8 mb-3 tracking-wider">Resultados Clave</h3>
                        <div class="grid grid-cols-2 gap-3">
                            ${Object.entries(cap.resultados || {}).map(([k, v]) => `
                                <div class="bg-black/20 p-3 rounded border border-white/5">
                                    <dt class="text-[9px] uppercase text-elephant-500 font-bold mb-1">${k.replace(/_/g, ' ')}</dt>
                                    <dd class="text-base font-mono text-cyan-400">${typeof v === 'number' ? v.toFixed(4) : v}</dd>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div class="flex flex-col">
                        <h3 class="text-xs font-bold uppercase text-elephant-400 mb-3 tracking-wider">Evidencia Visual</h3>
                        <div id="${idGrafico}" class="w-full h-full min-h-[350px] bg-black/5 rounded-xl border border-white/5"></div>
                    </div>
                </div>
            </div>
        `;

        contenedor.insertAdjacentHTML('beforeend', html);
        
        if (cap.grafico_datos) {
            setTimeout(() => this.renderGraficoPlotly(cap.grafico_datos, idGrafico), 50);
        }
    },

    renderGraficoPlotly(cfg, targetId) {
        const traces = [];
        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#72dcee', size: 10, family: 'Inter' },
            margin: { t: 20, b: 40, l: 40, r: 20 },
            showlegend: false,
            xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zeroline: false },
            yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zeroline: false }
        };

        if (cfg.tipo === 'histograma' || cfg.tipo === 'boxplot') {
            traces.push({
                x: cfg.tipo === 'histograma' ? cfg.data : null,
                y: cfg.tipo === 'boxplot' ? cfg.data : null,
                type: cfg.tipo,
                marker: { color: '#32c4de', line: { color: '#fff', width: 0.5 } },
                opacity: 0.7
            });
        } else if (cfg.tipo === 'hipotesis') {
            traces.push({
                x: cfg.x, y: cfg.y,
                type: 'scatter', mode: 'lines',
                fill: 'tozeroy',
                line: { color: '#16a7c4', width: 2 },
                name: 'Distribución'
            });
            if (cfg.t_stat !== undefined) {
                traces.push({
                    x: [cfg.t_stat, cfg.t_stat],
                    y: [0, Math.max(...cfg.y)],
                    mode: 'lines',
                    line: { color: '#ff4d4d', width: 3, dash: 'dash' },
                    name: 'T-obs'
                });
            }
        }

        Plotly.newPlot(targetId, traces, layout, { responsive: true, displayModeBar: false });
    },

    toggleLoading(show) {
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) indicator.classList.toggle('hidden', !show);
    },

    notify(msg, type = 'success') {
        const container = document.getElementById('alert-container');
        if (!container) return;
        
        const div = document.createElement('div');
        div.className = `alert-requiem alert-${type}`;
        div.textContent = msg;
        container.appendChild(div);
        
        setTimeout(() => {
            div.style.opacity = '0';
            div.style.transition = 'opacity 0.5s';
            setTimeout(() => div.remove(), 500);
        }, 4000);
    },

    enableAnalysisButton() {
        const btn = document.getElementById('btn-analizar');
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('cursor-not-allowed', 'opacity-50');
        }
    },

    mostrarVistaPrevia(stats, targetId) {
        const el = document.getElementById(targetId);
        if (el && stats) {
            el.innerHTML = `
                <div class="flex items-center gap-4 text-[11px] font-mono">
                    <span class="text-cyan-500">● MUESTRA:</span> 
                    <span>n=${stats.n}</span>
                    <span class="text-elephant-600">|</span>
                    <span>μ=${stats.media.toFixed(3)}</span>
                    <span class="text-elephant-600">|</span>
                    <span>s=${stats.std.toFixed(3)}</span>
                </div>`;
            el.classList.remove('hidden');
        }
    },

    mostrarDatosCrudos(datos, targetId, limite = 1000) { 
        const el = document.getElementById(targetId);
        if (!el || !datos || datos.length === 0) return;

        const muestra = datos.slice(0, limite);
        let html = '';

        if (typeof muestra[0] === "object" && muestra[0] !== null) {
            const columnas = Object.keys(muestra[0]);
            html = `
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr>
                            ${columnas.map(c => `<th class="p-2 border-b border-cyan-800 text-cyan-400 uppercase text-[9px]">${c}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${muestra.map(fila => `
                            <tr>
                                ${columnas.map(c => `<td class="p-2 border-b border-white/5 text-elephant-200">${fila[c]}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>`;
        } else {
            html = `
                <div class="grid grid-cols-5 gap-2">
                    ${muestra.map(val => `<div class="bg-white/5 p-2 rounded text-center text-cyan-300 font-mono text-[10px] border border-white/5">${typeof val === 'number' ? val.toFixed(2) : val}</div>`).join('')}
                </div>
                <p class="text-[9px] text-elephant-500 mt-3 italic text-right">* Datos generados por motor aleatorio</p>`;
        }

        el.innerHTML = html;
        el.classList.remove("hidden");
    },

    togglePreview() {
        const panel = document.getElementById("previewDatos");
        const btnSpan = document.querySelector("#btnPreview span");

        if (!panel) return;

        if (panel.classList.contains("hidden")) {
            if (!this.datosCrudos || this.datosCrudos.length === 0) {
                this.notify("No hay datos cargados para mostrar", "error");
                return;
            }
            this.mostrarDatosCrudos(this.datosCrudos, "previewDatos");
            panel.classList.remove("hidden");
            if (btnSpan) btnSpan.innerText = "▼ Ocultar datos cargados";
        } else {
            panel.classList.add("hidden");
            if (btnSpan) btnSpan.innerText = "▶ Ver datos crudos cargados";
        }
    }
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => app.init());
