// Estado local del juego
let gameState = {
    oro: 0,
    plots: []
};

// Cargar el juego al iniciar la página
document.addEventListener("DOMContentLoaded", () => {
    loadGameState();
    
    // Bucle de crecimiento: Cada 2 segundos las plantas crecen en el servidor
    setInterval(() => {
        fetch('/api/game/tick', { method: 'POST' })
            .then(() => loadGameState());
    }, 2000);
});

// Obtener datos actualizados del servidor
function loadGameState() {
    fetch('/api/game/state')
        .then(res => res.json())
        .then(data => {
            gameState.oro = data.oro;
            gameState.plots = data.plots;
            updateUI();
        })
        .catch(err => console.error("Error cargando estado:", err));
}

// Pintar los datos en la pantalla HTML
function updateUI() {
    // Actualizar marcador de oro (Asegúrate de que tu elemento HTML tenga id="gold-display" o similar)
    const goldDisplay = document.getElementById('gold-count') || document.getElementById('gold-display');
    if (goldDisplay) goldDisplay.innerText = gameState.oro;

    // Renderizar la Granja
    const grid = document.getElementById('farm-grid');
    if (!grid) return;
    grid.innerHTML = '';

    gameState.plots.forEach(p => {
        const tile = document.createElement('div');
        tile.className = "relative rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all border-2 p-4 h-24 w-24 text-center ";
        
        let visual = "🕳️"; // Vacío por defecto
        
        if (p.status === 'growing') {
            tile.className += "bg-amber-800 border-amber-950 text-white";
            visual = "🌱";
        } else if (p.status === 'ready') {
            tile.className += "bg-amber-600 border-orange-500 animate-pulse text-white";
            visual = "🥕";
        } else {
            tile.className += "bg-emerald-800 border-emerald-950 text-white hover:bg-emerald-700";
        }

        tile.innerHTML = `
            <span class="text-3xl">${visual}</span>
            ${p.status === 'growing' ? `<span class="text-xs block mt-1">${p.grow_progress}%</span>` : ''}
            ${p.status === 'ready' ? `<span class="text-xs block font-bold text-yellow-300 mt-1">¡LISTO!</span>` : ''}
            ${p.status === 'empty' ? `<span class="text-xs block text-emerald-200 mt-1">Sembrar</span>` : ''}
        `;

        tile.onclick = () => handleTileClick(p.plot_index);
        grid.appendChild(tile);
    });
}

// Manejar los clics en la tierra
function handleTileClick(index) {
    fetch('/api/game/click', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plot_index: index })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            if(data.oro_ganado > 0) {
                console.log(`¡Cosechaste oro! +${data.oro_ganado}`);
            }
            loadGameState(); // Recargar cambios al instante
        }
    });
}

// ==========================================
// SISTEMA DE QUIZ INTERACTIVO (ESTILO DUOLINGO)
// ==========================================
function openQuizChallenge() {
    const modal = document.getElementById('modal-quiz');
    if (!modal) {
        alert("No encontré el contenedor modal-quiz en tu HTML.");
        return;
    }
    
    fetch('/api/game/quiz/next')
        .then(res => res.json())
        .then(quiz => {
            if (quiz.error) {
                alert("¡No hay quizes configurados en este momento!");
                return;
            }
            
            // Mostrar ventana modal
            modal.classList.remove('hidden');
            modal.classList.add('flex');

            // Inyectar textos del Quiz en el modal
            document.getElementById('quiz-question').innerText = quiz.pregunta;
            
            const codeBox = document.getElementById('quiz-code');
            if(codeBox) codeBox.innerText = quiz.codigo || "";

            // Configurar botones de respuesta dinámicamente
            setupQuizOption('btn-opt-a', 'A', quiz.opcion_a, quiz.id);
            setupQuizOption('btn-opt-b', 'B', quiz.opcion_b, quiz.id);
            setupQuizOption('btn-opt-c', 'C', quiz.opcion_c, quiz.id);
        });
}

function setupQuizOption(elementId, letra, texto, quizId) {
    const btn = document.getElementById(elementId);
    if (!btn) return;
    btn.innerText = `(${letra}) ${texto}`;
    btn.onclick = () => enviarRespuestaQuiz(quizId, letra);
}

function enviarRespuestaQuiz(quizId, letra) {
    fetch('/api/game/quiz/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz_id: quizId, respuesta: letra })
    })
    .then(res => res.json())
    .then(data => {
        alert(data.message);
        if (data.correct) {
            closeQuiz();
            loadGameState();
        }
    });
}

function closeQuiz() {
    const modal = document.getElementById('modal-quiz');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}