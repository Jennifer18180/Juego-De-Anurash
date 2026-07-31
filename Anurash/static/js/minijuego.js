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
    // Iniciar temporizador de cuenta regresiva
    temporizadorId = setInterval(() => {
        tiempoRestante--;
        textoTiempo.textContent = tiempoRestante;
        
        if (tiempoRestante <= 0) {
            terminarJuego(false);
        }
    }, 1000);

    // Iniciar aparición de flores cada 800 milisegundos
    aparicionId = setInterval(mostrarFlorAleatoria, 800);
}

function mostrarFlorAleatoria() {
    // Ocultar todas las flores primero
    todasLasFlores.forEach(flor => flor.classList.add('flor-oculta'));
    
    // Elegir una casilla al azar (del 0 al 8)
    const indiceAleatorio = Math.floor(Math.random() * todasLasFlores.length);
    const florElegida = todasLasFlores[indiceAleatorio];
    
    // Mostrar la flor elegida
    florElegida.classList.remove('flor-oculta');
}

function atraparFlor(florElement) {
    // Si la flor está visible, la atrapamos
    if (!florElement.classList.contains('flor-oculta')) {
        puntuacion++;
        textoPuntuacion.textContent = puntuacion;
        florElement.classList.add('flor-oculta'); // La ocultamos al tocarla
        
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
    grid.style.display = 'none'; // Ocultar el tablero
    mensajeFinal.style.display = 'block';

    if (victoria) {
        textoResultado.textContent = "¡Conseguiste 10 flores! Ganaste una ranita 🐸";
        enviarVictoriaAlServidor();
    } else {
        textoResultado.textContent = "Se acabó el tiempo. ¡Inténtalo de nuevo!";
    }
}

function enviarVictoriaAlServidor() {
    // ¡Aquí nos comunicamos con Python (Flask)!
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
            // Actualizar visualmente la barra superior si quisiéramos, 
            // aunque al volver al mapa (botón) se actualizará sola gracias a Jinja.
        }
    })
    .catch(error => console.error('Error al contactar con el servidor:', error));
}

// Iniciar el juego en cuanto cargue la página
window.onload = iniciarJuego;