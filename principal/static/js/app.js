const app = {
    sessionId: null,

    init() {
        console.log('Requiem Engine 3.0.5 Inicializado');
        this.setupEventListeners();
        this.checkHealth();
    },

    setupEventListeners() {
        document.getElementById('csvFile')?.addEventListener('change', (e) => {
            if (e.target.files.length > 0) this.uploadCSV();
        });
    },

    // --- COMUNICACIÓN API ---
    
    async checkHealth() {
        try {
            await fetch('/api/analisis_rapido', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: 'ping'}) 
            });
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
                this.enableAnalysisButton();
                this.notify(`Datos cargados: ${d.datos.filas_validas} registros`, 'success');
                this.mostrarVistaPrevia(d.estadisticas, 'vista-previa');
            } else {
                this.notify(d.error || 'Error al procesar el archivo CSV', 'error');
            }
        } catch (error) {
            this.notify('Error de conexión', 'error');
        } finally {
            this.toggleLoading(false);
            fileInput.value = '';
        }
    },

    async generarEjemplo() {
        const payload = {
            n: parseInt(document.getElementById('nEjemplo').value) || 100,
            media: parseFloat(document.getElementById('mediaEjemplo').value) || 5.0,
            desviacion: parseFloat(document.getElementById('desvEjemplo').value) || 1.5
        };

        this.toggleLoading(true);
        try {
            const r = await fetch('/api/generar_ejemplo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const d = await r.json();
            
            if (r.ok && d.success) {
                this.sessionId = d.session_id;
                this.enableAnalysisButton();
                this.notify('Simulación generada', 'success');
                this.mostrarVistaPrevia(d.estadisticas, 'vista-previa-ejemplo');
            }
        } catch (error) {
            this.notify('Error en simulación', 'error');
        } finally {
            this.toggleLoading(false);
        }
    },

    async ejecutarAnalisis() {
        if (!this.sessionId) return this.notify('Cargue datos para iniciar', 'warning');

        const contenedor = document.getElementById('contenedor-analisis');
        const params = {
            session_id: this.sessionId,
            umbral: parseFloat(document.getElementById('input-umbral').value) || 5.0,
            nivel_confianza: parseFloat(document.getElementById('nivel-confianza').value) || 0.95
        };

        this.toggleLoading(true);
        contenedor.innerHTML = ''; 
        
        try {
            const r = await fetch('/api/analisis_completo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            const data = await r.json();

            if (r.ok) {
                const capKeys = ['capitulo1_descriptiva', 'capitulo2_estimacion', 'capitulo3_intervalos', 'capitulo4_hipotesis', 'capitulo5_comparacion'];
                
                let currentBatch = 0;
                const renderBatch = () => {
                    if (currentBatch < capKeys.length) {
                        const key = capKeys[currentBatch];
                        if (data[key]) {
                            this.renderCapitulo(data[key], currentBatch);
                        }
                        currentBatch++;
                        requestAnimationFrame(() => setTimeout(renderBatch, 50));
                    } else {
                        // FORZAR RENDERIZADO MATEMÁTICO AL FINAL
                        this.triggerMathJax(contenedor);
                        this.toggleLoading(false);
                        this.notify('Análisis finalizado', 'success');
                    }
                };
                renderBatch();

            } else {
                this.notify(data.error, 'error');
                this.toggleLoading(false);
            }
        } catch (error) {
            this.notify('Fallo crítico', 'error');
            this.toggleLoading(false);
        }
    },

    // --- MOTOR MATEMÁTICO ---

    triggerMathJax(element) {
        if (window.MathJax && window.MathJax.typesetPromise) {
            console.log("Iniciando motor MathJax...");
            // Pequeño delay para asegurar que el DOM insertado es estable
            setTimeout(() => {
                MathJax.typesetPromise([element])
                    .then(() => console.log("Fórmulas procesadas correctamente"))
                    .catch((err) => {
                        console.error("Fallo MathJax:", err);
                        // Respaldo sincrónico si falla la promesa
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
            <div class="glass-card p-8 mb-10 border-t-2 border-elephant-400 animate-slideIn">
                <div class="mb-4">
                    <span class="text-[10px] font-mono text-elephant-400 uppercase tracking-widest">Módulo Estadístico ${index + 1}</span>
                    <h2 class="text-2xl font-bold text-white">${cap.titulo}</h2>
                </div>
                <p class="text-elephant-300 mb-6 text-sm leading-relaxed">${cap.descripcion}</p>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                        <h3 class="text-xs font-bold uppercase text-elephant-400 mb-3 tracking-wider">Desarrollo Matemático</h3>
                        <div class="desarrollo-pasos-container min-h-[100px] text-white">
                            ${cap.formulas.latex}
                        </div>
                        
                        <h3 class="text-xs font-bold uppercase text-elephant-400 mt-8 mb-3 tracking-wider">Resultados Clave</h3>
                        <div class="grid grid-cols-2 gap-3">
                            ${Object.entries(cap.resultados).map(([k, v]) => `
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
            traces.push({
                x: [cfg.t_stat, cfg.t_stat],
                y: [0, Math.max(...cfg.y)],
                mode: 'lines',
                line: { color: '#ff4d4d', width: 3, dash: 'dash' },
                name: 'T-obs'
            });
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
        div.className = `alert-requiem alert-${type} animate-slideIn`;
        div.textContent = msg;
        container.appendChild(div);
        setTimeout(() => {
            div.style.opacity = '0';
            setTimeout(() => div.remove(), 500);
        }, 4000);
    },

    enableAnalysisButton() {
        const btn = document.getElementById('btn-analizar');
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = "1";
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
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());