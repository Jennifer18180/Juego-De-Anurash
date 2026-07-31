// static/js/minijuego.js

let puntuacion = 0;
let tiempoRestante = 30;
const metaFlores = 10;
let temporizadorId;
let aparicionId;

// Referencias a los elementos del HTML
const textoPuntuacion = document.getElementById('puntuacion');
const textoTiempo = document.getElementById('tiempo-restante');
const mensajeFinal = document.getElementById('mensaje-final');
const textoResultado = document.getElementById('texto-resultado');
const grid = document.querySelector('.estanque-grid');
const todasLasFlores = document.querySelectorAll('.flor-animada');

function iniciarJuego() {
    temporizadorId = setInterval(() => {
        tiempoRestante--;
        textoTiempo.textContent = tiempoRestante;
        
        if (tiempoRestante <= 0) {
            terminarJuego(false);
        }
    }, 1000);

    aparicionId = setInterval(mostrarFlorAleatoria, 800);
}

function mostrarFlorAleatoria() {
    todasLasFlores.forEach(flor => flor.classList.add('flor-oculta'));
    
    const indiceAleatorio = Math.floor(Math.random() * todasLasFlores.length);
    const florElegida = todasLasFlores[indiceAleatorio];
    
    florElegida.classList.remove('flor-oculta');
}

function atraparFlor(florElement) {
    if (!florElement.classList.contains('flor-oculta')) {
        puntuacion++;
        textoPuntuacion.textContent = puntuacion;
        florElement.classList.add('flor-oculta');
        
        // Comprobar si ganamos
        if (puntuacion >= metaFlores) {
            terminarJuego(true);
        }
    }
}

function terminarJuego(victoria) {
    clearInterval(temporizadorId);
    clearInterval(aparicionId);
    
    todasLasFlores.forEach(flor => flor.classList.add('flor-oculta'));
    grid.style.display = 'none';
    mensajeFinal.style.display = 'block';

    if (victoria) {
        textoResultado.textContent = "¡Conseguiste 10 flores! Ganaste una ranita";
        enviarVictoriaAlServidor();
    } else {
        textoResultado.textContent = "Se acabó el tiempo. ¡Inténtalo de nuevo!";
    }
}

function enviarVictoriaAlServidor() {
    fetch('/api/ganar_ranita', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log("Servidor responde:", data);
        if(data.success) {
        }
    })
    .catch(error => console.error('Error al contactar con el servidor:', error));
}

window.onload = iniciarJuego;