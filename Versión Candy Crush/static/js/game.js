// ============================================================================
// CODE & CROP - REPOSITORIO DE CONTROL REACTIVO COMPLETO (PYTHON-ONLY EDITION)
// ============================================================================

// Banderas de control de estado estricto
let isQuizActive = false; 
let lastKnownGold = 0;
let currentPlotsState = [];
let playerLevel = 1;
let playerXP = 0;
let unlockedCrops = ['carrot'];
let activeCrop = 'carrot';
let boughtAccessories = [];
let equippedAccessory = '';
let frogsCount = 0;
let maxFrogs = 4;
let maxPlots = 16;
let quizzesList = [];

// Banderas para el ciclo de sincronización pasiva con el backend
let needsServerSync = false;

// Configuración matemática de cultivos según el plan
const CROP_GROWTH_TIMES = {
    'vacio': 1.0,
    'carrot': 8.0,
    'wheat': 20.0,
    'pumpkin': 50.0,
    'watermelon': 100.0
};

const CROP_VALUES = {
    'vacio': 0,
    'dirt': 0,
    'carrot': 10.0,
    'wheat': 30.0,
    'pumpkin': 100.0,
    'watermelon': 350.0
};

const ACCESSORY_MULTIPLIERS = {
    'top_hat': 1.1,
    'sunglasses': 1.3,
    'gold_crown': 1.8
};

// ============================================================================
// INICIALIZACIÓN DEL ENTORNO DE JUEGO
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
    // Sincronización inicial estricta con el servidor Flask
    forceStateSync();
    
    // Bucle del cliente para actualizar animaciones y barras de progreso en tiempo real (200ms)
    setInterval(clientGameLoop, 200);

    // Bucle de sincronización pasiva periódica con el servidor (Cada 3 segundos)
    setInterval(() => {
        if (needsServerSync && !isQuizActive) {
            forceStateSync();
            needsServerSync = false;
        }
    }, 3000);

    // Escuchador dinámico para el selector manual de semillas en la UI
    const cropSelector = document.getElementById('crop-selector');
    if (cropSelector) {
        cropSelector.addEventListener('change', (e) => {
            selectActiveCrop(e.target.value);
        });
    }
});

// ============================================================================
// BUCLE DE JUEGO DEL CLIENTE (INTERFAZ REACTIVA COHESIVA)
// ============================================================================
function clientGameLoop() {
    if (currentPlotsState.length === 0) return;

    let localChangesMade = false;

    currentPlotsState.forEach(plot => {
        // Ignorar parcelas que excedan el límite desbloqueado por el nivel del usuario
        if (plot.plot_index >= maxPlots) return;

        // Simular crecimiento local si está en estado de crecimiento (growing)
        if (plot.status === 'growing') {
            const totalDuration = CROP_GROWTH_TIMES[plot.cultivo] || 10.0;
            // Incrementar progreso en proporción al paso del tiempo real (0.2s)
            plot.grow_progress += (0.2 / totalDuration) * 100;

            if (plot.grow_progress >= 100) {
                plot.grow_progress = 100;
                plot.status = 'ready';
                localChangesMade = true;
                needsServerSync = true; 
            }
        }
    });

    if (localChangesMade || document.querySelectorAll('.progress-bar-fill').length === 0) {
        updateIsometricGridProgress();
    } else {
        // Actualizar visualmente los anchos de barra sin redibujar el DOM completo
        currentPlotsState.forEach(plot => {
            if (plot.plot_index >= maxPlots) return;
            const bar = document.getElementById(`bar-fill-${plot.plot_index}`);
            if (bar) {
                bar.style.width = `${Math.min(100, plot.grow_progress)}%`;
            }
        });
    }
}

// ============================================================================
// SINCRONIZACIÓN ABSOLUTA CON BACKEND (FLASK STATE SYNC)
// ============================================================================
function forceStateSync() {
    fetch('/api/game/state')
        .then(res => {
            if (res.status === 401) {
                window.location.href = '/login';
                return null;
            }
            return res.json();
        })
        .then(data => {
            if (!data || data.status === 'error') return;

            // Sincronizar variables de control reactivo local
            playerLevel = data.level;
            playerXP = data.xp;
            unlockedCrops = data.unlocked_crops || ['carrot'];
            activeCrop = data.active_crop || 'carrot';
            frogsCount = data.frogs_count || 0;
            maxFrogs = data.max_frogs || 4;
            maxPlots = data.max_plots || 16;
            equippedAccessory = data.equipped_accessory || '';
            currentPlotsState = data.plots || [];

            // Animación fluida de incremento numérico para el contador de oro
            animateGoldCounter(data.gold);
            
            // Re-renderizar la interfaz estructural
            updateSidebarStats();
            renderPlotsGrid();
            renderChallengePanel(data.completed_quizzes || []);
        })
        .catch(err => console.error("Error crítico en sincronización de estado de la granja:", err));
}

// Animación de conteo de Monedas de Oro
function animateGoldCounter(targetGold) {
    const goldDisplay = document.getElementById('player-gold');
    if (!goldDisplay) return;

    if (lastKnownGold === targetGold) {
        goldDisplay.innerText = Number(targetGold).toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        return;
    }

    let current = lastKnownGold;
    const step = (targetGold - current) / 5; 
    let iterations = 0;

    const interval = setInterval(() => {
        current += step;
        iterations++;
        goldDisplay.innerText = Number(current).toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        
        if (iterations >= 5) {
            clearInterval(interval);
            goldDisplay.innerText = Number(targetGold).toLocaleString('es-ES', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
            lastKnownGold = targetGold;
        }
    }, 40);
}

// ============================================================================
// ACTUALIZACIÓN DE ESTADÍSTICAS Y ELEMENTOS DE LA BARRA LATERAL
// ============================================================================
function updateSidebarStats() {
    // Actualizar Nivel y barra de Experiencia (XP) de usuario (Límite 300 XP por nivel)
    const lvlText = document.getElementById('user-level');
    if (lvlText) lvlText.innerText = playerLevel;

    const xpText = document.getElementById('user-xp-text');
    if (xpText) xpText.innerText = `${playerXP}/300 XP`;

    const xpBar = document.getElementById('user-xp-bar');
    if (xpBar) {
        const percentage = Math.min(100, (playerXP / 300) * 100);
        xpBar.style.width = `${percentage}%`;
    }

    // Actualizar ranitas compradas y límites dinámicos por nivel
    const frogsTxt = document.getElementById('frogs-ratio');
    if (frogsTxt) frogsTxt.innerText = `${frogsCount}/${maxFrogs} Ranitas`;

    // Sincronizar dinámicamente el selector de semillas activas
    const cropSelector = document.getElementById('crop-selector');
    if (cropSelector) {
        cropSelector.innerHTML = '';
        const cropTranslations = { 'carrot': '🥕 Zanahoria', 'wheat': '🌾 Trigo', 'pumpkin': '🎃 Calabaza', 'watermelon': '🍉 Sandía' };
        
        unlockedCrops.forEach(crop => {
            const option = document.createElement('option');
            option.value = crop;
            option.text = cropTranslations[crop] || crop;
            option.selected = (crop === activeCrop);
            cropSelector.appendChild(option);
        });
    }

    // Actualizar los estados visuales en la tienda de semillas (Licencias de cultivos)
    ['wheat', 'pumpkin', 'watermelon'].forEach(crop => {
        const btn = document.getElementById(`buy-license-${crop}`);
        if (btn) {
            if (unlockedCrops.includes(crop)) {
                btn.className = "w-full bg-stone-700 text-gray-400 py-1.5 rounded-xl font-bold uppercase text-xs cursor-not-allowed";
                btn.innerText = "Desbloqueado";
                btn.disabled = true;
            } else {
                btn.disabled = false;
            }
        }
    });

    // Actualizar accesorios cosméticos equipados
    ['top_hat', 'sunglasses', 'gold_crown'].forEach(acc => {
        const btn = document.getElementById(`buy-acc-${acc}`);
        if (btn) {
            if (equippedAccessory === acc) {
                btn.className = "w-full bg-emerald-600 text-white py-1.5 rounded-xl font-bold uppercase text-xs cursor-default";
                btn.innerText = "Equipado";
            }
        }
    });
}

// ============================================================================
// RENDERIZADO DE CUADRÍCULA DE PARCELAS DISPONIBLES SEGÚN EL NIVEL
// ============================================================================
function renderPlotsGrid() {
    const gridContainer = document.getElementById('plots-grid');
    if (!gridContainer) return;
    
    gridContainer.innerHTML = '';
    
    // Adaptación estructural de rejilla según el nivel (Nivel 1: 4x4, Resto: 8x8)
    if (playerLevel === 1) {
        gridContainer.className = "grid grid-cols-4 gap-4 max-w-xl mx-auto p-4";
    } else {
        gridContainer.className = "grid grid-cols-8 gap-3 max-w-5xl mx-auto p-4";
    }

    currentPlotsState.forEach(p => {
        // Ocultar de forma estricta las parcelas que queden fuera del límite actual del nivel
        if (p.plot_index >= maxPlots) return;

        const tile = document.createElement('div');
        tile.id = `plot-tile-${p.plot_index}`;
        tile.className = "relative aspect-square bg-stone-700/30 border border-[#4a3e36] rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-stone-600/40 transition-all shadow-md select-none p-1 overflow-hidden animate__animated animate__fadeIn";
        tile.onclick = () => handlePlotInteraction(p.plot_index);
        
        // Elemento interno para renderizar el cultivo o el estado del terreno
        const spriteContainer = document.createElement('div');
        spriteContainer.id = `plot-sprite-${p.plot_index}`;
        spriteContainer.className = "text-3xl transition-transform duration-300 hover:scale-110 select-none z-10";
        tile.appendChild(spriteContainer);

        // Barra de progreso de crecimiento interna
        const progressBar = document.createElement('div');
        progressBar.className = "absolute bottom-1.5 left-2 right-2 h-2 bg-stone-900/60 rounded-full overflow-hidden hidden border border-stone-950/20";
        progressBar.id = `progress-container-${p.plot_index}`;
        
        const progressFill = document.createElement('div');
        progressFill.id = `bar-fill-${p.plot_index}`;
        progressFill.className = "h-full bg-gradient-to-r from-amber-500 to-emerald-500 transition-all duration-200 progress-bar-fill";
        progressFill.style.width = "0%";
        
        progressBar.appendChild(progressFill);
        tile.appendChild(progressBar);

        // Indicador de Automatización por Bloque (Renderizado de Ranita en 2D en esquina)
        // 1 Ranita maneja 4 parcelas consecutivas (Bloques: 0-3, 4-7, 8-11, etc.)
        const activeFrogIndex = Math.floor(p.plot_index / 4);
        if (activeFrogIndex < frogsCount) {
            const frogLabel = document.createElement('span');
            frogLabel.className = "absolute top-1 right-1 text-xs bg-emerald-900/80 px-1 rounded border border-emerald-500 text-[10px] select-none font-mono animate__animated animate__bounceIn";
            // Renderizar la ranita con su respectivo accesorio global si está equipado
            let frogEmoji = "🐸";
            if (equippedAccessory === 'top_hat') frogEmoji = "🎩🐸";
            if (equippedAccessory === 'sunglasses') frogEmoji = "😎🐸";
            if (equippedAccessory === 'gold_crown') frogEmoji = "👑🐸";
            
            frogLabel.innerHTML = frogEmoji;
            tile.appendChild(frogLabel);
        }

        // Renderizar índice numérico discreto de la parcela para guiar al jugador
        const indexLabel = document.createElement('span');
        indexLabel.className = "absolute bottom-0.5 right-1.5 text-[9px] font-mono text-stone-500 select-none";
        indexLabel.innerText = p.plot_index;
        tile.appendChild(indexLabel);

        gridContainer.appendChild(tile);
    });

    updateIsometricGridProgress();
}

// Sincronizar estados visuales de los emojis e íconos de barra de carga
function updateIsometricGridProgress() {
    currentPlotsState.forEach(p => {
        if (p.plot_index >= maxPlots) return;

        const sprite = document.getElementById(`plot-sprite-${p.plot_index}`);
        const barContainer = document.getElementById(`progress-container-${p.plot_index}`);
        const barFill = document.getElementById(`bar-fill-${p.plot_index}`);

        if (!sprite) return;

        // Diccionario visual de emojis según la etapa de crecimiento
        const cropVisuals = {
            'carrot': { growing: '🌱', ready: '🥕' },
            'wheat': { growing: '🌿', ready: '🌾' },
            'pumpkin': { growing: '🍃', ready: '🎃' },
            'watermelon': { growing: '🌸', ready: '🍉' }
        };

        if (p.cultivo === 'vacio') {
            sprite.innerText = '🪨'; // Terreno virgen/piedra
            if (barContainer) barContainer.classList.add('hidden');
        } else if (p.cultivo === 'dirt') {
            sprite.innerText = '🟫'; // Terreno arado listo para sembrar
            if (barContainer) barContainer.classList.add('hidden');
        } else {
            // El terreno contiene un cultivo real activo
            const stages = cropVisuals[p.cultivo];
            if (stages) {
                if (p.status === 'growing') {
                    sprite.innerText = stages.growing;
                    if (barContainer) barContainer.classList.remove('hidden');
                    if (barFill) barFill.style.width = `${p.grow_progress}%`;
                } else {
                    sprite.innerText = stages.ready;
                    if (barContainer) barContainer.classList.add('hidden');
                }
            }
        }
    });
}

// ============================================================================
// LOGICA DE INTERACCIÓN DIRECTA CON LAS PARCELAS DE LA GRANJA
// ============================================================================
function handlePlotInteraction(plotIndex) {
    if (isQuizActive) return;

    const plot = currentPlotsState.find(p => p.plot_index === plotIndex);
    if (!plot) return;

    // Si la parcela está automatizada por un bloque de ranita, no requiere clicks manuales
    const activeFrogIndex = Math.floor(plotIndex / 4);
    if (activeFrogIndex < frogsCount && plot.cultivo !== 'vacio' && plot.cultivo !== 'dirt') {
        return; 
    }

    // Acción 1: Arar la tierra si está en estado vacío/roca
    if (plot.cultivo === 'vacio') {
        executeClickAction(plotIndex, 'click');
        return;
    }

    // Acción 2: Sembrar si está arada (dirt), o Cosechar si está lista (ready)
    const clickAction = (plot.cultivo === 'dirt') ? 'plant' : 'harvest';
    // Si se intenta interactuar y sigue en crecimiento (growing) de forma manual, no hace nada
    if (plot.status === 'growing') return;

    executeClickAction(plotIndex, clickAction);
}

function executeClickAction(plotIndex, actionName) {
    fetch('/api/game/click', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plot_index: plotIndex, action: actionName })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            if (data.gold_gained > 0) {
                spawnFloatingGoldEffect(plotIndex, data.gold_gained);
            }
            forceStateSync();
        }
    })
    .catch(err => console.error("Error al procesar click en la parcela:", err));
}

// Efecto visual de Monedas Flotantes al interactuar
function spawnFloatingGoldEffect(plotIndex, amount) {
    const tile = document.getElementById(`plot-tile-${plotIndex}`);
    if (!tile) return;

    const floatText = document.createElement('div');
    floatText.className = "absolute text-amber-400 font-black text-sm z-50 pointer-events-none floating-gold select-none animate__animated animate__fadeOutUp";
    floatText.innerText = `+🪙${amount}`;
    
    tile.appendChild(floatText);
    setTimeout(() => floatText.remove(), 1000);
}

// ============================================================================
// PANEL DE CUESTIONARIOS ESTRUCTURADO (3 NIVELES - 15 COMPLEJOS MODULARES)
// ============================================================================
function renderChallengePanel(completedGroups) {
    const challengesContainer = document.getElementById('challenges-list');
    if (!challengesContainer) return;
    
    challengesContainer.innerHTML = '';
    
    // Títulos de los 15 grupos estructurales de Python reales mapeados en tu backend
    const groupTitles = {
        1: "Variables y Operadores", 2: "Tipos de Datos", 3: "Estructuras If-Else",
        4: "Listas y Métodos", 5: "Bucles For & range()", 6: "Diccionarios & Sets",
        7: "Funciones def", 8: "Excepciones & Archivos", 9: "List Comprehensions",
        10: "Métodos de Cadenas", 11: "Clases y Objetos", 12: "Métodos Estáticos",
        13: "Generadores", 14: "Manejo with", 15: "Módulos Mágicos"
    };

    // Mapear el nivel del cuestionario según el grupo de pertenencia
    // Grupo 1-5 Fácil, 6-10 Medio, 11-15 Difícil
    for (let id = 1; id <= 15; id++) {
        const isCompleted = completedGroups.includes(id);
        
        let difficultyBadge = `<span class="px-1.5 py-0.5 text-[8px] rounded font-bold bg-green-900/50 text-green-400 border border-green-700/40 uppercase">Fácil</span>`;
        if (id > 5 && id <= 10) {
            difficultyBadge = `<span class="px-1.5 py-0.5 text-[8px] rounded font-bold bg-amber-900/50 text-amber-400 border border-amber-700/40 uppercase">Medio</span>`;
        } else if (id > 10) {
            difficultyBadge = `<span class="px-1.5 py-0.5 text-[8px] rounded font-bold bg-red-900/50 text-red-400 border border-red-700/40 uppercase">Difícil</span>`;
        }

        const btn = document.createElement('button');
        
        if (isCompleted) {
            btn.className = "w-full text-left p-3 bg-emerald-950/20 border-2 border-emerald-500/50 rounded-xl flex justify-between items-center opacity-90 select-none cursor-default mb-2";
            btn.innerHTML = `
                <div>
                    <div class="flex items-center gap-2 mb-0.5">
                        <p class="text-[10px] font-mono tracking-wider text-gray-400 uppercase">CUESTIONARIO ${id}</p>
                        ${difficultyBadge}
                    </div>
                    <h4 class="text-xs font-bold text-gray-300 line-through decoration-emerald-500/50">${groupTitles[id] || 'Tema Python'}</h4>
                </div>
                <span class="text-base">✅</span>
            `;
        } else {
            btn.className = "w-full text-left p-3 bg-[#1e1b18]/40 border-2 border-[#4a3e36] rounded-xl flex justify-between items-center hover:border-[#ea580c] hover:bg-stone-800/40 transition-all cursor-pointer mb-2 animate__animated animate__fadeInUp";
            btn.innerHTML = `
                <div>
                    <div class="flex items-center gap-2 mb-0.5">
                        <p class="text-[10px] font-mono tracking-wider text-[#ea580c] uppercase">CUESTIONARIO ${id}</p>
                        ${difficultyBadge}
                    </div>
                    <h4 class="text-xs font-bold text-white">${groupTitles[id] || 'Tema Python'}</h4>
                </div>
                <span class="text-xs bg-stone-700 text-amber-400 px-1.5 py-0.5 rounded font-mono font-bold">📜 Play</span>
            `;
            btn.onclick = () => launchQuizSequence(id, 0); // Iniciar secuencia de 3 preguntas (step 0)
        }
        
        challengesContainer.appendChild(btn);
    }
}

// Lanzador de flujo modular de Cuestionarios en la Interfaz
function launchQuizSequence(groupId, stepIndex) {
    isQuizActive = true;

    fetch(`/api/game/quizzes?group_id=${groupId}&step=${stepIndex}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'error') {
                alert(data.message);
                closeQuizModal();
                return;
            }

            // Inyectar datos en la plantilla del Modal estructural
            document.getElementById('quiz-title').innerText = `DESAFÍO PYTHON - PASO ${stepIndex + 1}/3`;
            document.getElementById('quiz-question').innerText = data.question;

            const codeBox = document.getElementById('quiz-code');
            if (data.code_snippet) {
                codeBox.innerText = data.code_snippet;
                codeBox.classList.remove('hidden');
            } else {
                codeBox.classList.add('hidden');
            }

            // Construcción reactiva de los botones de opciones múltiples (A, B, C, D)
            const optionsContainer = document.getElementById('quiz-options');
            optionsContainer.innerHTML = '';

            const optionsMap = [
                { key: 'A', value: data.option_a },
                { key: 'B', value: data.option_b },
                { key: 'C', value: data.option_c },
                { key: 'D', value: data.option_d }
            ];

            optionsMap.forEach(opt => {
                if (!opt.value) return;
                const btnOpt = document.createElement('button');
                btnOpt.className = "w-full text-left p-3 bg-stone-800 border border-[#4a3e36] rounded-xl text-xs font-bold text-gray-200 hover:bg-stone-700 hover:border-amber-500 transition-all cursor-pointer flex gap-3";
                btnOpt.innerHTML = `<span class="text-amber-500 font-mono">[${opt.key}]</span> <span>${opt.value}</span>`;
                btnOpt.onclick = () => submitQuizAnswer(groupId, stepIndex, opt.key);
                optionsContainer.appendChild(btnOpt);
            });

            // Configurar el botón de pistas (hint)
            const hintBtn = document.getElementById('btn-hint');
            if (hintBtn) {
                hintBtn.onclick = () => {
                    alert(`💡 PISTA PYTHON:\n${data.hint || 'Analiza cuidadosamente las reglas de sintaxis del lenguaje.'}`);
                };
            }

            // Mostrar el modal quitando la clase oculta
            const modal = document.getElementById('quiz-modal');
            if (modal) modal.classList.remove('hidden');
        })
        .catch(err => {
            console.error("Error al cargar pregunta del cuestionario:", err);
            closeQuizModal();
        });
}

// Procesar el envío de la respuesta al backend de Flask
function submitQuizAnswer(groupId, stepIndex, selectedOption) {
    fetch('/api/game/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            group_id: groupId,
            step: stepIndex,
            option: selectedOption
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);

        if (data.correct) {
            if (data.completed) {
                // Si el backend marcó completed=True, superó el paso 2 con éxito completo
                closeQuizModal();
                forceStateSync();
            } else {
                // Avanzar automáticamente al siguiente paso del mismo grupo (step + 1)
                launchQuizSequence(groupId, stepIndex + 1);
            }
        } else {
            // Si falla cualquier paso intermedio, el cuestionario se cancela y debe reintentarse desde el paso 0
            closeQuizModal();
            forceStateSync();
        }
    })
    .catch(err => console.error("Error al evaluar respuesta:", err));
}

function closeQuizModal() {
    const modal = document.getElementById('quiz-modal');
    if (modal) modal.classList.add('hidden');
    isQuizActive = false;
}

// ============================================================================
// FUNCIONES ADICIONALES DE ADQUISICIÓN DE TIENDA Y CONFIGURACIONES
// ============================================================================
function selectActiveCrop(cropName) {
    fetch('/api/game/select_crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ crop: cropName })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            activeCrop = cropName;
            forceStateSync();
        }
    });
}

function buyCropLicense(cropName) {
    fetch('/api/game/buy_license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ crop: cropName })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        forceStateSync();
    });
}

function buyAutomatorFrog() {
    fetch('/api/game/buy_frog', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        forceStateSync();
    });
}

function buyAccessory(accessoryName) {
    fetch('/api/game/buy_accessory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accessory: accessoryName })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        forceStateSync();
    });
}