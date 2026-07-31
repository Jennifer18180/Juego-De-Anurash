from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

# --- SIMULACIÓN DE BASE DE DATOS ---
# Usamos esta clase para simular los datos de tu usuario. 
# En el futuro, esto lo conectaremos a una base de datos SQL real.
class Usuario:
    def __init__(self):
        self.ranitas_actuales = 1  # Empieza con 1 vida para que pruebes el minijuego
        self.monedas = 150         # Unas cuantas monedas iniciales
        self.nivel_actual = 2      # Nivel desbloqueado en el mapa

# Creamos a nuestro jugador principal
jugador = Usuario()

# --- RUTAS DE PANTALLAS (FRONT-END) ---

@app.route('/')
def mapa():
    """Ruta principal: Muestra el mapa (el estanque)."""
    return render_template('mapa.html', usuario=jugador)

@app.route('/reclamar_recompensa', methods=['POST'])
def reclamar_recompensa():
    # Sumamos las 50 monedas usando la notación correcta
    recompensa = 50
    jugador.monedas += recompensa 
    
    return jsonify({
        "status": "success",
        "monedas_totales": jugador.monedas,
        "mensaje": "¡50 monedas añadidas con éxito!"
    })


# Diccionario para inyectar descripciones didácticas automáticas a los quizes de la DB
DESCRIPCIONES_QUIZ = {
    1: "Domina la sintaxis esencial, tipos de datos básicos y operadores matemáticos fundamentales en Python.",
    2: "Desafía tu lógica con estructuras de datos, manejo de archivos y funciones más elaboradas.",
    3: "Pon a prueba tu experiencia con decoradores, asincronía, paralelismo y las últimas características del lenguaje."
}

# Nuestra "Base de datos" de preguntas por nivel
datos_quiz = {
    "basico": [
        {
            "pregunta": "¿Cuál es la salida correcta de este código? `print(type(5.0))`", 
            "opciones": ["<class 'int'>", "<class 'float'>", "<class 'double'>", "str"],
            "respuesta_correcta": "<class 'float'>" 
        },
        {
            "pregunta": "¿Cómo se declara una variable de texto (string) válida?", 
            "opciones": ["x = Hola", "x -> 'Hola'", "x = 'Hola'", "String x = 'Hola'"],
            "respuesta_correcta": "x = 'Hola'" 
        },
        {
            "pregunta": "¿Qué operador calcula el residuo de una división?", 
            "opciones": ["/", "//", "%", "**"],
            "respuesta_correcta": "%" 
        },
        {
            "pregunta": "¿Qué método se usa para convertir un texto a mayúsculas?", 
            "opciones": ["capitalize", "upper", "toupper", "uppercase"],
            "respuesta_correcta": "upper" 
        }
    ],
    "intermedio": [
        {
            "pregunta": "¿Cuál es la salida de la siguiente List Comprehension? `resultado = [x*2 for x in range(3)]`", 
            "opciones": ["[0, 1, 2]", "[0, 2, 4]", "[2, 4, 6]", "Error de sintaxis"],
            "respuesta_correcta": "[0, 2, 4]" 
        },
        {
            "pregunta": "¿Qué método de diccionario se usa para obtener un valor sin que falle con un KeyError si la clave no existe?", 
            "opciones": ["fetch", "pop", "get", "retrieve"],
            "respuesta_correcta": "get" 
        },
        {
            "pregunta": "¿Qué palabra clave se utiliza para enviar un valor de retorno al llamador de una función?", 
            "opciones": ["yield", "break", "send", "return"],
            "respuesta_correcta": "return" 
        },
        {
            "pregunta": "¿Cuál es la forma recomendada para abrir y cerrar un archivo de forma segura?", 
            "opciones": ["open('datos.txt')", "with open('datos.txt') as f:", "file.open('datos.txt')", "read('datos.txt')"],
            "respuesta_correcta": "with open('datos.txt') as f:" 
        }
    ],
    "avanzado": [
        {
            "pregunta": "¿Qué es fundamentalmente un decorador en Python?", 
            "opciones": [
                "Una clase que hereda de múltiples padres", 
                "Una función que toma otra función como argumento para extender su comportamiento", 
                "Un módulo para pintar la interfaz gráfica", 
                "Un tipo de variable estática"
            ],
            "respuesta_correcta": "Una función que toma otra función como argumento para extender su comportamiento" 
        },
        {
            "pregunta": "¿Cuál es el núcleo operativo de la biblioteca asíncrona `asyncio`?", 
            "opciones": [
                "Un sistema de hilos (Threading)", 
                "El Global Interpreter Lock (GIL)", 
                "Un bucle de eventos (Event Loop) que maneja tareas concurrentes", 
                "Un recolector de basura iterativo"
            ],
            "respuesta_correcta": "Un bucle de eventos (Event Loop) que maneja tareas concurrentes" 
        },
        {
            "pregunta": "¿Qué módulo permite saltarse las restricciones del GIL ejecutando cómputo pesado en núcleos de CPU paralelos?", 
            "opciones": ["threading", "asyncio", "multiprocessing", "subprocess"],
            "respuesta_correcta": "multiprocessing" 
        },
        {
            "pregunta": "¿Qué potente sistema de control estructural de flujo se introdujo formalmente en Python 3.10?", 
            "opciones": ["switch / case", "match / case", "do / while", "try / except / else"],
            "respuesta_correcta": "match / case" 
        }
    ]
}

@app.route('/quiz/<int:nivel_id>')
def quiz(nivel_id):
    if jugador.ranitas_actuales <= 0:
        return redirect(url_for('minijuego'))
    
    # 1. Creamos un traductor de números a las llaves de tu diccionario
    mapa_niveles = {
        1: "basico",
        2: "intermedio",
        3: "avanzado"
    }
    
    # 2. Convertimos el ID (ej: 1) en el texto (ej: "basico")
    nivel_texto = mapa_niveles.get(nivel_id, "basico")
    
    # 3. Extraemos las preguntas correspondientes
    datos_pregunta = datos_quiz.get(nivel_texto)
        
    # Le enviamos la lista de preguntas al HTML
    return render_template('quiz.html', usuario=jugador, nivel=nivel_id, datos=datos_pregunta)

@app.route('/minijuego')
def minijuego():
    # Renderizamos la pantalla del minijuego de emergencia
    return render_template('minijuego.html', usuario=jugador)

@app.route('/ganar_minijuego', methods=['POST'])
def ganar_minijuego():
    # Corregimos también la notación de las ranitas aquí
    if jugador.ranitas_actuales == 0:
        jugador.ranitas_actuales = 1
        return jsonify({"status": "success", "mensaje": "¡Minijuego superado! Recuperas 1 vida."})
    
    return jsonify({"status": "info", "mensaje": "Ya tienes vidas suficientes."})

@app.route('/tienda')
def tienda():
    # Mostramos la tienda pasando los datos del usuario para ver sus monedas actuales
    return render_template('tienda.html', usuario=jugador)

@app.route('/comprar_item', methods=['POST'])
def comprar_item():
    # Extraemos los datos que nos envía el JavaScript de la tienda
    datos = request.get_json()
    tipo_item = datos.get('tipo')
    precio = int(datos.get('precio'))
    
    # 1. Verificamos si el jugador tiene suficiente dinero usando notación de punto
    if jugador.monedas >= precio:
        
        # 2. Lógica dependiendo de qué objeto compró
        if tipo_item == 'vida':
            if jugador.ranitas_actuales < 3:
                jugador.monedas -= precio
                jugador.ranitas_actuales += 1
                mensaje = "¡Has recuperado una ranita! 🐸"
            else:
                return jsonify({"status": "error", "mensaje": "Ya tienes todas tus ranitas listas. No necesitas gastar en esto."})
                
        else:
            # Lógica para Lupa o Escudo
            jugador.monedas -= precio
            
            # Si el jugador aún no tiene un inventario, se lo creamos como un atributo
            if not hasattr(jugador, 'inventario'):
                jugador.inventario = []
                
            # Guardamos el ítem en su inventario
            jugador.inventario.append(tipo_item)
            
            nombre = "Lupa de Pistas" if tipo_item == 'lupa' else "Escudo de Hoja"
            mensaje = f"¡Has comprado {nombre} con éxito! ⛺"
            
        # 3. Devolvemos el éxito y los datos actualizados
        return jsonify({
            "status": "success",
            "monedas_restantes": jugador.monedas,
            "mensaje": mensaje
        })
        
    # Si no le alcanza el dinero
    return jsonify({
        "status": "error",
        "mensaje": "¡No tienes suficientes monedas para comprar este artículo!"
    })

# --- RUTAS DE API (BACK-END / LÓGICA OCULTA) ---

@app.route('/api/ganar_ranita', methods=['POST'])
def ganar_ranita():
    """
    Ruta secreta que llama JavaScript cuando ganas el minijuego.
    Suma una vida si el jugador tiene menos de 3.
    """
    global jugador
    
    if jugador.ranitas_actuales < 3:
        jugador.ranitas_actuales += 1
        mensaje = "¡Vida recuperada!"
    else:
        mensaje = "¡Ya tienes las vidas al máximo!"

    # Devolvemos una respuesta en JSON para que JavaScript la lea
    return jsonify({
        'success': True,
        'ranitas_actuales': jugador.ranitas_actuales,
        'mensaje': mensaje
    })

@app.route('/api/restar_ranita', methods=['POST'])
def restar_ranita():
    """
    Ruta para cuando el jugador se equivoca en una pregunta del quiz.
    (Puedes conectarla en el futuro desde tu quiz.js)
    """
    global jugador
    
    if jugador.ranitas_actuales > 0:
        jugador.ranitas_actuales -= 1
        
    return jsonify({
        'success': True,
        'ranitas_actuales': jugador.ranitas_actuales
    })

@app.route('/usar_item', methods=['POST'])
def usar_item():
    datos = request.get_json()
    tipo_item = datos.get('tipo')
    
    # Verificamos que el jugador tenga el atributo y el ítem exista en su lista
    if hasattr(jugador, 'inventario') and tipo_item in jugador.inventario:
        jugador.inventario.remove(tipo_item)
        return jsonify({"status": "success", "mensaje": f"{tipo_item} consumido."})
        
    return jsonify({"status": "error", "mensaje": "No posees este objeto."})

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == '__main__':
    # debug=True hace que el servidor se reinicie solo si haces cambios en el código
    app.run(debug=True, port=5000)