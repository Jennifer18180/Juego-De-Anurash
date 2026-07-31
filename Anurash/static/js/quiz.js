// static/js/quiz.js

function verificarRespuesta(boton, esCorrecta) {
    // 1. Bloqueamos todos los botones para que el usuario no haga doble clic
    const botones = document.querySelectorAll('.boton-opcion');
    botones.forEach(b => b.classList.add('deshabilitado'));

    // 2. Obtenemos el elemento de la imagen de la rana
    const ranaAvatar = document.getElementById('rana-avatar');

    if (esCorrecta) {
        // --- SI ACIERTA ---
        boton.classList.add('correcto');
        // Cambiamos a la rana feliz
        ranaAvatar.src = '/static/img/rana_feliz.png';
        
        // Aquí luego enviaremos a Flask que gane Monedas/XP
        
    } else {
        // --- SI FALLA ---
        boton.classList.add('incorrecto');
        // Cambiamos a la rana triste
        ranaAvatar.src = '/static/img/rana_triste.png';
        
        // Buscamos cuál era el botón correcto y lo pintamos de verde para enseñarle al usuario
        // (En el futuro, esto lo validaremos desde el servidor)
    }

    // 3. Simulamos pasar a la siguiente pregunta después de 2 segundos
    setTimeout(() => {
        // Restauramos los botones
        botones.forEach(b => {
            b.classList.remove('deshabilitado', 'correcto', 'incorrecto');
        });
        
        // Volvemos a la rana pensativa para la nueva pregunta
        ranaAvatar.src = '/static/img/rana_pensativa.png';
        
        // (Aquí recargaríamos la página o inyectaríamos la siguiente pregunta con Flask)
        console.log("Siguiente pregunta...");
    }, 2000);
}