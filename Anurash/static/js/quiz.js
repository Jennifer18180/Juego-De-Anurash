// static/js/quiz.js

function verificarRespuesta(boton, esCorrecta) {
    const botones = document.querySelectorAll('.boton-opcion');
    botones.forEach(b => b.classList.add('deshabilitado'));

    const ranaAvatar = document.getElementById('rana-avatar');

    if (esCorrecta) {
        // --- SI ACIERTA ---
        boton.classList.add('correcto');
        // Cambiamos a la rana feliz
        ranaAvatar.src = '/static/img/rana_feliz.png';
        
        
    } else {
        // --- SI FALLA ---
        boton.classList.add('incorrecto');
        // Cambiamos a la rana triste
        ranaAvatar.src = '/static/img/rana_triste.png';
    }

    setTimeout(() => {
        // Restauramos los botones
        botones.forEach(b => {
            b.classList.remove('deshabilitado', 'correcto', 'incorrecto');
        });
        
        ranaAvatar.src = '/static/img/rana_pensativa.png';
        
        console.log("Siguiente pregunta...");
    }, 2000);
}