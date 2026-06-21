// ============================================================================
// CODE & CROP - REPOSITORIO DE CONTROL REACTIVO COMPLETO (EDICIÓN ANURASH)
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
let maxFrogs = 0;
let maxPlots = 16;
let completedQuizzes = [];

// Temporizador de sincronización pasiva en tiempo real (1 segundo)
const SYNC_INTERVAL_MS = 1000;

// Configuración matemática y visual de los cultivos de la granja
const CROP_EMOJIS = {
    'vacio': '🕳️',
    'dirt': '🟫',
    'carrot': '🥕',
    'wheat': '🌾',
    'pumpkin': '🎃',
    'watermelon': '🍉'
};

const CROP_NAMES = {
    'carrot': 'Zanahoria',
    'wheat': 'Trigo',
    'pumpkin': 'Calabaza',
    'watermelon': 'Sandía'
};

// Variables globales temporales para controlar el paso actual de los cuestionarios en 3 niveles
let currentQuizGroupId = null;
let currentQuizStep = 0;

// Inicialización de arranque nativa cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
    // Sincronización inicial rápida del estado de la granja
    forceStateSync();
    setupLeaderboardLoop();

    // Loop persistente para simular el crecimiento visual continuo y la sincronización pasiva
    setInterval(() => {
        if (!isQuizActive) {
            // Actualización incremental local suave para evitar parpadeos visuales
            currentPlotsState.forEach(plot => {
                if (plot.status === 'growing') {
                    const times = { 'carrot': 8.0, 'wheat': 20.0, 'pumpkin': 50.0, 'watermelon': 100.0 };
                    const totalTime = times[plot.cultivo] || 10.0;
                    plot.grow_progress += (1.0 / totalTime) * 100.0;
                    if (plot.grow_progress >= 100.0) {
                        plot.grow_progress = 100.0;
                        plot.status = 'ready';
                    }
                }
            });
            renderPlotsGrid();
        }
    }, 1000);

    // Loop secundario de sincronización con la base de datos de SQLite en Flask
    setInterval(() => {
        if (!isQuizActive) {
            forceStateSync();
        }
    }, 4000);
});

// ============================================================================
// SISTEMA DE RENDERIZACIÓN VISUAL DE LA GRANJA Y PARCELAS ORIGINALES
// ============================================================================
function forceStateSync() {
    fetch('/api/game/state')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'error') return;

            // Sincronizar variables locales
            playerLevel = data.level;
            playerXP = data.xp;
            unlockedCrops = data.unlocked_crops;
            activeCrop = data.active_crop;
            equippedAccessory = data.equipped_accessory;
            frogsCount = data.frogs_count;
            maxFrogs = data.max_frogs;
            maxPlots = data.max_plots;
            completedQuizzes = data.completed_quizzes || [];
            currentPlotsState = data.plots;

            // Renderizar los componentes principales del fronted
            updateUserInterfaceHeaders(data.gold);
            updateCropSelectorDropdown();
            renderPlotsGrid();
            renderChallengePanel();
        })
        .catch(err => console.error("Error sincronizando estado:", err));
}

function updateUserInterfaceHeaders(gold) {
    // Animación de incremento numérico para el Oro de Anurash
    const goldDisplay = document.getElementById("player-gold");
    if (goldDisplay) {
        goldDisplay.innerText = parseFloat(gold).toFixed(1);
    }

    // Actualización de nivel y barra de Experiencia (XP)
    const levelDisplay = document.getElementById("user-level");
    if (levelDisplay) levelDisplay.innerText = playerLevel;

    const xpText = document.getElementById("user-xp-text");
    if (xpText) xpText.innerText = `${playerXP}/300 XP`;

    const xpBar = document.getElementById("user-xp-bar");
    if (xpBar) {
        const pct = Math.min(100, (playerXP / 300) * 100);
        xpBar.style.width = `${pct}%`;
    }

    // Ratio de ranitas activas por bloques fijos
    const frogsRatio = document.getElementById("frogs-ratio");
    if (frogsRatio) {
        frogsRatio.innerText = `${frogsCount}/${maxFrogs} Ranitas`;
    }
}

function updateCropSelectorDropdown() {
    const selector = document.getElementById("crop-selector");
    if (!selector) return;

    // Guardar selección actual del usuario
    const currentSelection = selector.value || activeCrop;
    selector.innerHTML = "";

    unlockedCrops.forEach(crop => {
        const option = document.createElement("option");
        option.value = crop;
        option.text = `🌱 Sembrar: ${CROP_NAMES[crop] || crop.toUpperCase()}`;
        if (crop === currentSelection) {
            option.selected = true;
        }
        selector.appendChild(option);
    });

    // Escuchador de cambios reactivo para modificar la semilla activa del backend
    selector.onchange = (e) => {
        fetch('/api/game/select_crop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ crop: e.target.value })
        }).then(() => forceStateSync());
    };
}

function renderPlotsGrid() {
    const grid = document.getElementById("plots-grid");
    if (!grid) return;

    grid.innerHTML = "";

    // Filtrar y renderizar únicamente la porción permitida según el nivel actual (level * 16)
    const visiblePlots = currentPlotsState.slice(0, maxPlots);

    visiblePlots.forEach(plot => {
        const plotCell = document.createElement("div");
        
        // Clases de estilo visual e interactivo de tus parcelas anteriores
        let bgClass = "bg-[#3d3025] border-[#4a3e36]"; // Por defecto vacío
        
        if (plot.cultivo === 'dirt') {
            bgClass = "bg-[#5c4033] border-[#704d3d]"; // Tierra arada clásica
        } else if (plot.status === 'growing') {
            bgClass = "bg-[#274227] border-[#365f36]"; // En crecimiento (Tono verdoso)
        } else if (plot.status === 'ready') {
            bgClass = "bg-[#155e3a] border-[#16a34a] animate__animated animate__pulse animate__infinite"; // Listo para cosechar
        }

        plotCell.className = `relative flex flex-col items-center justify-center border-4 rounded-xl p-2 cursor-pointer h-24 text-center transition-all shadow-md select-none ${bgClass}`;
        
        // Estructura interna de la parcela (Emoji central + Barra interna de crecimiento)
        let innerHTML = `<span class="text-3xl filter drop-shadow">${CROP_EMOJIS[plot.cultivo] || '🕳️'}</span>`;
        
        // Si tiene una ranita asignada en este bloque, pintar marcador visual
        if (plot.automatizada) {
            innerHTML += `<span class="absolute top-1 right-1 text-xs" title="Automatizado por Ranita">🐸</span>`;
        }

        // Barra de progreso de crecimiento interna original
        if (plot.status === 'growing') {
            innerHTML += `
                <div class="absolute bottom-1.5 left-2 right-2 bg-stone-900 h-2 rounded-full overflow-hidden p-0.5 border border-stone-700/50">
                    <div class="bg-gradient-to-r from-emerald-500 to-green-400 h-full rounded-full" style="width: ${plot.grow_progress}%"></div>
                </div>
            `;
        } else if (plot.status === 'ready') {
            innerHTML += `<span class="absolute bottom-0.5 text-[9px] font-mono tracking-tighter uppercase font-bold text-amber-300 drop-shadow">¡COSECHAR!</span>`;
        } else if (plot.cultivo === 'vacio') {
            innerHTML += `<span class="absolute bottom-1 text-[8px] font-mono text-gray-500 uppercase">Arar</span>`;
        } else if (plot.cultivo === 'dirt') {
            innerHTML += `<span class="absolute bottom-1 text-[8px] font-mono text-amber-500 uppercase">Plantar</span>`;
        }

        plotCell.innerHTML = innerHTML;

        // Disparador del clic manual unificado
        plotCell.onclick = () => handlePlotInteraction(plot);

        grid.appendChild(plotCell);
    });
}

function handlePlotInteraction(plot) {
    if (plot.automatizada) return; // Las parcelas administradas por ranitas no reciben clics manuales

    let action = 'click'; // Por defecto: arar 'vacio'
    if (plot.cultivo === 'dirt') action = 'plant';
    else if (plot.status === 'ready') action = 'harvest';
    else if (plot.status === 'growing') return; // Bloquear clics si está creciendo

    fetch('/api/game/click', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plot_index: plot.plot_index, action: action })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            if (data.gold_gained > 0) {
                spawnFloatingGoldEffect(plot.plot_index, data.gold_gained);
            }
            forceStateSync();
        }
    })
    .catch(err => console.error("Error al interactuar con parcela:", err));
}

// ============================================================================
// EFECTO VISUAL DE MONEDAS FLOTANTES SOBRE EL CAMPO (FLOATING GOLD)
// ============================================================================
function spawnFloatingGoldEffect(plotIndex, amount) {
    const grid = document.getElementById("plots-grid");
    if (!grid) return;

    const cells = grid.children;
    // Buscar la celda correspondiente al índice visible actual
    const maxPlotsVisible = playerLevel * 16;
    if (plotIndex >= maxPlotsVisible || !cells[plotIndex]) return;

    const targetCell = cells[plotIndex];
    const rect = targetCell.getBoundingClientRect();
    const gridRect = grid.getBoundingClientRect();

    const floatingText = document.createElement("div");
    floatingText.className = "floating-gold pixel-font font-black";
    floatingText.innerText = `+${parseFloat(amount).toFixed(0)}🪙`;

    // Posicionamiento preciso tridimensional flotante
    floatingText.style.left = `${rect.left - gridRect.left + rect.width / 2 - 15}px`;
    floatingText.style.top = `${rect.top - gridRect.top + 10}px`;

    grid.appendChild(floatingText);

    // Destrucción limpia del nodo DOM tras finalizar la animación CSS
    setTimeout(() => {
        floatingText.remove();
    }, 1000);
}

// ============================================================================
// RENDERIZADO Y CONTROL DEL PANEL LATERAL DE CUESTIONARIOS (3 PASOS CONSECUTIVOS)
// ============================================================================
function renderChallengePanel() {
    const listContainer = document.getElementById("challenges-list");
    if (!listContainer) return;

    listContainer.innerHTML = "";

    // Construcción de los 15 bloques modulares del plan de desarrollo
    for (let i = 1; i <= 15; i++) {
        const isCompleted = completedQuizzes.includes(i);
        const btn = document.createElement("button");

        let btnClass = "w-full text-left p-2.5 rounded-xl border text-xs font-bold transition-all flex justify-between items-center ";
        
        if (isCompleted) {
            btnClass += "bg-emerald-950/30 border-emerald-800 text-emerald-400 opacity-75 cursor-not-allowed";
        } else {
            btnClass += "bg-[#14110f]/80 border-[#3d3025] text-gray-200 hover:border-[#ea580c] hover:bg-[#221a14]";
        }

        btn.className = btnClass;
        btn.disabled = isCompleted;

        // Estructura interna del texto del cuestionario modular
        let badge = isCompleted ? "✅ Hecho" : "📝 Iniciar";
        btn.innerHTML = `
            <div class="flex flex-col">
                <span class="font-mono text-[10px] uppercase text-[#ea580c] font-black">Módulo Desafío #${i}</span>
                <span class="text-xs text-white mt-0.5">Evaluación Core Python</span>
            </div>
            <span class="text-[10px] font-mono uppercase bg-[#14110f] px-2 py-1 rounded-md border border-stone-800">${badge}</span>
        `;

        if (!isCompleted) {
            btn.onclick = () => openQuizChallenge(i, 0);
        }

        listContainer.appendChild(btn);
    }
}

function openQuizChallenge(groupId, step) {
    if (isQuizActive) return;

    currentQuizGroupId = groupId;
    currentQuizStep = step;

    fetch(`/api/game/quizzes?group_id=${groupId}&step=${step}`)
        .then(res => res.json())
        .then(data => {
            if (data.status === 'error') return;

            isQuizActive = true;
            
            // Inyectar datos al Modal interactivo central
            document.getElementById("quiz-title").innerText = `DESAFÍO #${groupId} - PASO ${step + 1}/3`;
            document.getElementById("quiz-question").innerText = data.question;

            const codeBlock = document.getElementById("quiz-code");
            if (data.code_snippet && data.code_snippet.trim() !== "") {
                codeBlock.innerText = data.code_snippet;
                codeBlock.classList.remove("hidden");
            } else {
                codeBlock.classList.add("hidden");
            }

            // Configurar el botón de pista integrado en el modal
            const hintBtn = document.getElementById("btn-hint");
            hintBtn.onclick = () => {
                alert(`💡 PISTA: ${data.hint}`);
            };

            // Inyectar las 4 opciones interactivas de respuesta
            const optionsContainer = document.getElementById("quiz-options");
            optionsContainer.innerHTML = "";

            const options = [
                { key: 'A', text: data.option_a },
                { key: 'B', text: data.option_b },
                { key: 'C', text: data.option_c },
                { key: 'D', text: data.option_d }
            ];

            options.forEach(opt => {
                const optBtn = document.createElement("button");
                optBtn.className = "w-full text-left bg-[#14110f] border-2 border-[#3d3025] hover:border-[#ea580c] text-xs font-bold text-gray-300 p-3 rounded-xl transition-all cursor-pointer flex items-center gap-2";
                optBtn.innerHTML = `<span class="bg-[#ea580c]/20 text-[#ea580c] px-1.5 py-0.5 rounded font-mono">${opt.key}</span> ${opt.text}`;
                
                optBtn.onclick = () => submitQuizAnswer(opt.key);
                optionsContainer.appendChild(optBtn);
            });

            // Mostrar el modal removiendo la clase 'hidden'
            document.getElementById("quiz-modal").classList.remove("hidden");
        })
        .catch(err => console.error("Error cargando cuestionario:", err));
}

function submitQuizAnswer(selectedOption) {
    fetch('/api/game/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            group_id: currentQuizGroupId,
            step: currentQuizStep,
            option: selectedOption
        })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        
        if (data.status === 'success' && data.correct) {
            if (data.completed) {
                // Fin exitoso del paso 3. Cerrar todo y sincronizar
                closeQuizModal();
                forceStateSync();
            } else {
                // Avanzar inmediatamente al siguiente paso consecutivo (Paso + 1)
                isQuizActive = false; // reset temporal para permitir la recarga
                openQuizChallenge(currentQuizGroupId, currentQuizStep + 1);
            }
        } else {
            // Error o respuesta incorrecta, cancelar bloque completo de inmediato
            closeQuizModal();
            forceStateSync();
        }
    })
    .catch(err => console.error("Error al enviar respuesta:", err));
}

function closeQuizModal() {
    document.getElementById("quiz-modal").classList.add("hidden");
    isQuizActive = false;
    currentQuizGroupId = null;
    currentQuizStep = 0;
}

// ============================================================================
// FUNCIONES ADICIONALES DE LA TIENDA DE MERCADO Y LEADERBOARD COMPETITIVO
// ============================================================================
function buyAutomatorFrog() {
    fetch('/api/game/buy_frog', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            forceStateSync();
        });
}

function buyCropLicense(crop) {
    fetch('/api/game/buy_license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ crop: crop })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        forceStateSync();
    });
}

function buyAccessory(acc) {
    fetch('/api/game/buy_accessory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accessory: acc })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        forceStateSync();
    });
}

function setupLeaderboardLoop() {
    const fetchLeaderboard = () => {
        fetch('/api/game/leaderboard')
            .then(res => res.json())
            .then(data => {
                const container = document.getElementById("leaderboard-list");
                if (!container) return;
                container.innerHTML = "";
                
                data.forEach((player, idx) => {
                    const row = document.createElement("div");
                    row.className = "flex justify-between items-center text-xs font-mono py-1 border-b border-[#3d3025]/30 text-gray-300";
                    row.innerHTML = `
                        <span>${idx + 1}. ${player.username}</span>
                        <span class="text-amber-400 font-bold">${player.gold.toFixed(1)} 🪙</span>
                    `;
                    container.appendChild(row);
                });
            });
    };
    
    fetchLeaderboard();
    setInterval(fetchLeaderboard, 10000); // Refrescar ranking cada 10 segundos
}