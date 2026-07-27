import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ============================================================================
# MODELO DE USUARIO / AGRICULTOR DE ANURASH
# ============================================================================
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    # Economía y Progreso
    gold = db.Column(db.Float, default=100.0)
    total_gold_earned = db.Column(db.Float, default=100.0)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    
    # Mecánicas de la Granja
    unlocked_crops = db.Column(db.String(255), default="carrot")  # Separados por comas: e.g., "carrot,wheat"
    active_crop = db.Column(db.String(50), default="carrot")
    equipped_accessory = db.Column(db.String(50), default="")     # top_hat, sunglasses, gold_crown
    frogs_count = db.Column(db.Integer, default=0)                # Multiplicador de automatización por bloques
    
    # Auditoría e inventario histórico (Guardado modular de cuestionarios completados)
    bought_accessories = db.Column(db.Text, default="")           # Almacena "q_1,q_2" para cuestionarios resueltos
    last_sync = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relación inversa estricta de las 64 parcelas
    plots = db.relationship('Parcela', backref='usuario', lazy=True, cascade="all, delete-orphan")


# ============================================================================
# MODELO DE PARCELA (ESTRUCTURA DE MAPA FISICO PERSISTENTE)
# ============================================================================
class Parcela(db.Model):
    __tablename__ = 'parcelas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    plot_index = db.Column(db.Integer, nullable=False)            # Índices fijos del 0 al 63
    
    cultivo = db.Column(db.String(50), default="vacio")           # vacio, dirt, carrot, wheat, pumpkin, watermelon
    status = db.Column(db.String(50), default="idle")             # idle, growing, ready
    grow_progress = db.Column(db.Float, default=0.0)              # De 0.0 a 100.0 %
    automatizada = db.Column(db.Boolean, default=False)           # Calculado en base a bloques de ranitas


# ============================================================================
# MODELO DE CUESTIONARIOS CORE DE PYTHON
# ============================================================================
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_group_id = db.Column(db.Integer, nullable=False)         # Identificador del bloque de desafío (1 al 15)
    step = db.Column(db.Integer, nullable=False)                  # Pasos secuenciales indexados: 0, 1 o 2 (Paso 1, 2 y 3)
    difficulty = db.Column(db.String(20), default="easy")
    
    question = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text, default="")                 # Bloques opcionales de sintaxis a evaluar
    
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    
    correct_option = db.Column(db.String(1), nullable=False)       # 'A', 'B', 'C' o 'D'
    hint = db.Column(db.Text, default="")


# ============================================================================
# SIEMBRA AUTOMÁTICA DE CUESTIONARIOS REQUERIDOS (SEED DATA)
# ============================================================================
def seed_quizzes():
    """Inserta la base de cuestionarios de 3 pasos si la tabla se encuentra vacía."""
    if Quiz.query.first() is not None:
        return  # Evitar duplicaciones si ya existen datos precargados

    python_challenges = [
        # --- DESAFÍO 1: FUNDAMENTOS Y OPERADORES ---
        {
            "group_id": 1, "step": 0,
            "question": "¿Cuál es el resultado de evaluar la expresión 11 // 3 en Python?",
            "code_snippet": "resultado = 11 // 3\nprint(resultado)",
            "a": "3.666...", "b": "3", "c": "2", "d": "None", "correct": "B",
            "hint": "El operador // ejecuta una división entera, truncando el residuo decimal."
        },
        {
            "group_id": 1, "step": 1,
            "question": "¿Qué operador aritmético se utiliza para calcular la potencia de un número en Python?",
            "code_snippet": "base = 2\nexponente = 3\n# ¿Qué operador va aquí para obtener 8?",
            "a": "^", "b": "pow", "c": "**", "d": "exp", "correct": "C",
            "hint": "En Python, elevar un número a una potencia requiere el uso de dos asteriscos consecutivos."
        },
        {
            "group_id": 1, "step": 2,
            "question": "¿De qué tipo de dato nativo será la variable resultante tras ejecutar la operación 10 / 2?",
            "code_snippet": "x = 10 / 2\nprint(type(x))",
            "a": "<class 'int'>", "b": "<class 'float'>", "c": "<class 'double'>", "d": "<class 'decimal'>", "correct": "B",
            "hint": "El operador de división única / siempre produce un resultado de tipo float, incluso si el resultado es exacto."
        },

        # --- DESAFÍO 2: ESTRUCTURAS DE CONTROL ---
        {
            "group_id": 2, "step": 0,
            "question": "¿Qué palabra clave se utiliza en Python para encadenar múltiples condiciones condicionales alternativas?",
            "code_snippet": "if x > 0:\n    print('Positivo')\n# ¿Qué palabra va aquí?\n     print('Negativo')",
            "a": "else if", "b": "elseif", "c": "elif", "d": "switch", "correct": "C",
            "hint": "Python fusiona 'else' e 'if' en la estructura simplificada nativa 'elif'."
        },
        {
            "group_id": 2, "step": 1,
            "question": "¿Cuántas veces se imprimirá la palabra 'Anurash' en la consola con el siguiente ciclo?",
            "code_snippet": "for i in range(2, 5):\n    print('Anurash')",
            "a": "5 veces", "b": "3 veces", "c": "2 veces", "d": "4 veces", "correct": "B",
            "hint": "La función range(inicio, fin) es exclusiva en su límite superior. Evaluará los índices 2, 3 y 4."
        },
        {
            "group_id": 2, "step": 2,
            "question": "¿Qué hace la instrucción 'break' cuando se ejecuta dentro de un bucle while o for?",
            "code_snippet": "while True:\n    if condicion:\n        break",
            "a": "Pausa el bucle temporalmente", "b": "Salta a la siguiente iteración del ciclo", "c": "Finaliza y rompe inmediatamente el bucle", "d": "Reinicia el script", "correct": "C",
            "hint": "La instrucción break interrumpe de forma absoluta el ciclo actual y transfiere el control a la línea posterior al bucle."
        }
    ]

    # Bucle expansivo para autogenerar datos simulados del resto de los 15 desafíos del plan
    for g_id in range(3, 16):
        python_challenges.append({
            "group_id": g_id, "step": 0,
            "question": f"¿[Módulo {g_id} - Paso 1] Qué retorna la función nativa len() si se le pasa una lista vacía?",
            "code_snippet": "print(len([]))",
            "a": "None", "b": "0", "c": "1", "d": "Raises Error", "correct": "B", "hint": "Una estructura sin elementos tiene longitud cero."
        })
        python_challenges.append({
            "group_id": g_id, "step": 1,
            "question": f"¿[Módulo {g_id} - Paso 2] Cómo se añade un elemento al final de una lista en Python?",
            "code_snippet": "mi_lista = [1, 2]\n# ¿Qué método va aquí?",
            "a": "add()", "b": "push()", "c": "append()", "d": "insert()", "correct": "C", "hint": "El método append añade un elemento al final del contenedor mutante."
        })
        python_challenges.append({
            "group_id": g_id, "step": 2,
            "question": f"¿[Módulo {g_id} - Paso 3] Cuál es la salida correcta de este condicional booleano de control?",
            "code_snippet": "print(True and False)",
            "a": "True", "b": "False", "c": "None", "d": "Error", "correct": "B", "hint": "El operador lógico 'and' requiere que ambas expresiones sean verdaderas."
        })

    # Inyección controlada por transacciones a la base de datos
    for q in python_challenges:
        nuevo_quiz = Quiz(
            quiz_group_id=q["group_id"],
            step=q["step"],
            question=q["question"],
            code_snippet=q["code_snippet"],
            option_a=q["a"],
            option_b=q["b"],
            option_c=q["c"],
            option_d=q["d"],
            correct_option=q["correct"],
            hint=q["hint"]
        )
        db.session.add(nuevo_quiz)
        
    db.session.commit()