from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

app = Flask(__name__)

# --- SIMULACIÓN DE BASE DE DATOS ---
# Usamos esta clase para simular los datos de tu usuario. 
class Usuario:
    def __init__(self):
        self.ranitas_actuales = 1
        self.monedas = 150
        self.nivel_actual = 1
        self.inventario = []
        self.cosmetico= ''

jugador = Usuario()

app.secret_key = 'mi_ranita_secreta_123'

# --- RUTAS DE PANTALLAS (FRONT-END) ---

@app.route('/')
def mapa():
    """Ruta principal: Muestra el mapa (el estanque)."""
    return render_template('mapa.html', usuario=jugador)

@app.route('/reclamar_recompensa', methods=['POST'])
def reclamar_recompensa():
    datos = request.get_json()
    nivel_superado = datos.get('nivel_superado')
    
    jugador.monedas += 50 
    
    if nivel_superado == jugador.nivel_actual:
        jugador.nivel_actual += 1
        
    return jsonify({
        'status': 'success',
        'mensaje': '¡Recompensa reclamada y nivel actualizado!',
        'monedas_totales': jugador.monedas
    })

DESCRIPCIONES_QUIZ = {
    1: "Domina la sintaxis esencial, tipos de datos básicos y operadores matemáticos fundamentales en Python.",
    2: "Desafía tu lógica con estructuras de datos, manejo de archivos y funciones más elaboradas.",
    3: "Pon a prueba tu experiencia con decoradores, asincronía, paralelismo y las últimas características del lenguaje."
}

# Nuestra "Base de datos" de preguntas por nivel
niveles_python = {
    1: {
        "tema": "Print y Tipos de Datos",
        "apuntes": "La función <b>print()</b> muestra mensajes en la pantalla.<br><br>Tipos de datos mágicos:<br>- <b>String (Texto):</b> Va entre comillas, ej: 'Hola'<br>- <b>Integer (Entero):</b> Números sin decimales, ej: 5<br>- <b>Float (Decimal):</b> Números con punto, ej: 3.14",
        "preguntas": [
            {
                "pregunta": "¿Cuál es el código correcto para que la rana diga 'Croac'?",
                "opciones": ["print('Croac')", "mostrar('Croac')", "echo 'Croac'", "escribir('Croac')"],
                "respuesta_correcta": "print('Croac')"
            },
            {
                "pregunta": "¿Qué tipo de dato es el número 42?",
                "opciones": ["String (Texto)", "Integer (Entero)", "Float (Decimal)", "Boolean (Lógico)"],
                "respuesta_correcta": "Integer (Entero)"
            },
            {
                "pregunta": "¿Cómo se escribe correctamente un texto (String) en Python?",
                "opciones": ["Entre paréntesis ()", "Entre comillas ''", "Con un símbolo de dólar $", "Con asteriscos **"],
                "respuesta_correcta": "Entre comillas ''"
            }
        ]
    },
    2: {
        "tema": "Variables",
        "apuntes": "Una <b>variable</b> es como una caja o mochila que guarda datos para usarlos después.<br><br>Usamos el símbolo <b>=</b> para guardar un dato en la variable.<br>Ejemplo:<br><i>vidas = 3</i><br><i>nombre = 'Anurash'</i>",
        "preguntas": [
            {
                "pregunta": "¿Cómo guardas el número 10 en una variable llamada 'monedas'?",
                "opciones": ["monedas = 10", "10 = monedas", "var monedas : 10", "set monedas = 10"],
                "respuesta_correcta": "monedas = 10"
            },
            {
                "pregunta": "Si tienes 'x = 5' y luego escribes 'x = 8', ¿cuánto vale 'x' al final?",
                "opciones": ["5", "8", "Da un error", "13"],
                "respuesta_correcta": "8"
            },
            {
                "pregunta": "¿Cuál de estos nombres de variable NO es válido en Python?",
                "opciones": ["mi_rana", "rana1", "1rana", "rana_feliz"],
                "respuesta_correcta": "1rana"
            }
        ]
    },
    3: {
        "tema": "Operadores y Lógica",
        "apuntes": "Símbolos para matemáticas y comparaciones:<br><br><b>+</b> (Suma)<br><b>-</b> (Resta)<br><b>*</b> (Multiplicación)<br><b>==</b> (Pregunta si son iguales)<br><b>!=</b> (Pregunta si son diferentes)",
        "preguntas": [
            {
                "pregunta": "¿Qué resultado da la operación: 5 + 3 * 2?",
                "opciones": ["16", "11", "10", "22"],
                "respuesta_correcta": "11"
            },
            {
                "pregunta": "Para comprobar si dos variables son exactamente iguales, usamos:",
                "opciones": ["=", "==", "===", "=>"],
                "respuesta_correcta": "=="
            },
            {
                "pregunta": "¿Qué valor devuelve la expresión: 10 > 5?",
                "opciones": ["True (Verdadero)", "False (Falso)", "5", "10"],
                "respuesta_correcta": "True (Verdadero)"
            }
        ]
    },
    4: {
        "tema": "Condicionales (If/Else)",
        "apuntes": "Permiten que tu programa tome decisiones.<br><br><b>if</b> (Si pasa esto...)<br><b>else</b> (Si no, haz esto otro...)<br><br>¡Recuerda siempre dejar un espacio (sangría) dentro del if!",
        "preguntas": [
            {
                "pregunta": "¿Qué palabra clave se usa para ejecutar código cuando la condición del 'if' es falsa?",
                "opciones": ["then", "else", "except", "elif"],
                "respuesta_correcta": "else"
            },
            {
                "pregunta": "Es obligatorio usar esto después de la condición en un 'if':",
                "opciones": ["Un punto y coma (;)", "Dos puntos (:)", "Un punto (.)", "Una coma (,)"],
                "respuesta_correcta": "Dos puntos (:)"
            },
            {
                "pregunta": "¿Qué es la indentación (sangría) en Python?",
                "opciones": ["Un tipo de variable", "Los espacios al inicio de una línea para definir bloques de código", "Un error del sistema", "Una función matemática"],
                "respuesta_correcta": "Los espacios al inicio de una línea para definir bloques de código"
            }
        ]
    },
    5: {
        "tema": "Bucles Avanzados",
        "apuntes": "Sirven para repetir acciones sin escribir el código muchas veces.<br><br><b>For:</b> Repite un número exacto de veces (ej: iterar sobre una lista).<br><b>While:</b> Repite MIENTRAS una condición siga siendo verdadera.",
        "preguntas": [
            {
                "pregunta": "¿Qué bucle usarías si quieres repetir una acción exactamente 5 veces?",
                "opciones": ["Bucle while", "Bucle for", "Bucle if", "Bucle repeat"],
                "respuesta_correcta": "Bucle for"
            },
            {
                "pregunta": "¿Qué hace la función range(3) en un bucle for?",
                "opciones": ["Genera los números 1, 2, 3", "Genera los números 0, 1, 2", "Repite el código 4 veces", "Crea una lista vacía"],
                "respuesta_correcta": "Genera los números 0, 1, 2"
            },
            {
                "pregunta": "Un bucle 'while' se detiene cuando su condición se vuelve:",
                "opciones": ["Verdadera (True)", "Falsa (False)", "Cero", "Infinita"],
                "respuesta_correcta": "Falsa (False)"
            }
        ]
    },
    6: {
        "tema": "Listas y Colecciones",
        "apuntes": "Una <b>lista</b> guarda muchos elementos ordenados en una sola variable.<br><br>Se crean con corchetes <b>[ ]</b>.<br>¡Ojo! El primer elemento de una lista siempre está en la posición <b>0</b>.",
        "preguntas": [
            {
                "pregunta": "¿Cómo creas una lista vacía en Python?",
                "opciones": ["lista = ()", "lista = []", "lista = {}", "lista = ||"],
                "respuesta_correcta": "lista = []"
            },
            {
                "pregunta": "Si flores = ['Loto', 'Rosa', 'Lirio'], ¿cómo accedes a 'Loto'?",
                "opciones": ["flores[1]", "flores[0]", "flores.first()", "flores['Loto']"],
                "respuesta_correcta": "flores[0]"
            },
            {
                "pregunta": "¿Qué método usas para agregar un elemento al final de una lista?",
                "opciones": [".add()", ".insert()", ".append()", ".push()"],
                "respuesta_correcta": ".append()"
            }
        ]
    },
    7: {
        "tema": "Funciones Mágicas",
        "apuntes": "Son bloques de código que puedes reutilizar.<br><br>Se crean usando la palabra <b>def</b> seguida del nombre de la función y paréntesis.<br>Usamos <b>return</b> para devolver un resultado al final.",
        "preguntas": [
            {
                "pregunta": "¿Cuál es la palabra clave para definir (crear) una función en Python?",
                "opciones": ["function", "def", "crear", "func"],
                "respuesta_correcta": "def"
            },
            {
                "pregunta": "¿Cómo 'llamas' o ejecutas una función llamada 'saltar'?",
                "opciones": ["call saltar()", "saltar", "saltar()", "run saltar"],
                "respuesta_correcta": "saltar()"
            },
            {
                "pregunta": "¿Qué palabra se usa para que una función devuelva un valor al programa?",
                "opciones": ["send", "return", "output", "give"],
                "respuesta_correcta": "return"
            }
        ]
    }
}


@app.route('/quiz/<int:nivel>')
def quiz(nivel):
    #Verificar si el nivel existe en nuestra base de datos
    if nivel not in niveles_python:
        return redirect(url_for('mapa'))
    #Verificar si el usuario tiene este nivel desbloqueado
    if nivel > jugador.nivel_actual: 
        # Si intenta jugar el nivel 5 pero está en el 2, lo devolvemos al mapa
        return redirect(url_for('mapa'))
        
    datos_nivel = niveles_python[nivel]
    
    preguntas = datos_nivel['preguntas']
    apuntes = datos_nivel['apuntes']
    tema = datos_nivel['tema']
    
    return render_template(
        'quiz.html',
        nivel=nivel,
        tema=tema,
        datos=preguntas,
        apuntes=apuntes,
        usuario=jugador
    )

@app.route('/minijuego')
def minijuego():
    return render_template('minijuego.html', usuario=jugador)

@app.route('/ganar_minijuego', methods=['POST'])
def ganar_minijuego():
    if jugador.ranitas_actuales == 0:
        jugador.ranitas_actuales = 1
        return jsonify({"status": "success", "mensaje": "¡Minijuego superado! Recuperas 1 vida."})
    
    return jsonify({"status": "info", "mensaje": "Ya tienes vidas suficientes."})

@app.route('/tienda')
def tienda():
    return render_template('tienda.html', usuario=jugador)

@app.route('/comprar_item', methods=['POST'])
def comprar_item():
    datos = request.get_json()
    tipo_item = datos.get('tipo')
    precio = int(datos.get('precio'))
    
    if jugador.monedas >= precio:
        
        # 2. Lógica dependiendo de qué objeto compró
        if tipo_item == 'vida':
            if jugador.ranitas_actuales < 3:
                jugador.monedas -= precio
                jugador.ranitas_actuales += 1
                mensaje = "¡Has recuperado una ranita!"
            else:
                return jsonify({"status": "error", "mensaje": "Ya tienes todas tus ranitas listas. No necesitas gastar en esto."})
                
        else:
            jugador.monedas -= precio
            
            # Si el jugador aún no tiene un inventario, se lo creamos como un atributo
            if not hasattr(jugador, 'inventario'):
                jugador.inventario = []
                
            # Guardamos el ítem en su inventario
            jugador.inventario.append(tipo_item)
            
            nombre = "Lupa de Pistas" if tipo_item == 'lupa' else "Escudo de Hoja"
            mensaje = f"¡Has comprado {nombre} con éxito!"
            
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

@app.route('/comprar_cosmetico/<tipo>', methods=['POST'])
def comprar_cosmetico(tipo):
    precios = {
        'sombrero': 100,
        'collar': 150
    }
    
    # Validar que el ítem exista
    if tipo not in precios:
        flash('Ese artículo no existe.', 'error')
        return redirect(url_for('tienda'))

    precio = precios[tipo]

    # Verificar si tiene suficientes monedas usando PUNTO en lugar de corchetes
    if jugador.monedas >= precio:
        jugador.monedas -= precio
        jugador.cosmetico = tipo # Aquí le equipamos el ítem
        flash(f'¡Has comprado un {tipo.capitalize()}!', 'success')
    else:
        flash('No tienes suficientes monedas para este artículo.', 'error')
        
    return redirect(url_for('tienda'))

@app.route('/desequipar', methods=['POST'])
def desequipar():
    # Diccionario con los precios para saber cuánto devolver
    precios = {
        'sombrero': 100,
        'collar': 150
    }
    
    # Verificamos si el jugador tiene un cosmético equipado y si está en nuestra lista
    if jugador.cosmetico and jugador.cosmetico in precios:
        reembolso = precios[jugador.cosmetico]
        jugador.monedas += reembolso  # Le sumamos las monedas de vuelta
        
        item_devuelto = jugador.cosmetico # Guardamos el nombre para el mensaje
        jugador.cosmetico = None          # Desequipamos el ítem
        
        flash(f'¡Te has quitado el {item_devuelto} y recuperaste {reembolso} monedas!', 'success')
    else:
        flash('No llevabas ningún accesorio equipado.', 'error')
        
    return redirect(url_for('tienda'))

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)