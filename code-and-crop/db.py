import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db = SQLAlchemy()
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    gold = db.Column(db.Float, default=100.0)
    prestige_count = db.Column(db.Integer, default=0)
    active_language = db.Column(db.String(20), default='Python') # 'Python', 'SQL', 'JavaScript'
    total_gold_earned = db.Column(db.Float, default=0.0)
    last_sync = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    parcelas = db.relationship('Parcela', backref='dueno', lazy=True, cascade="all, delete-orphan")
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
class Parcela(db.Model):
    __tablename__ = 'parcelas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    posicion_x = db.Column(db.Integer, nullable=False)
    posicion_y = db.Column(db.Integer, nullable=False)
    cultivo = db.Column(db.String(20), default='vacio') # 'vacio', 'zanahoria', 'trigo', 'calabaza'
    status = db.Column(db.String(20), default='empty') # 'empty', 'growing', 'ready'
    grow_progress = db.Column(db.Float, default=0.0) # 0.0 to 100.0
    automatizada = db.Column(db.Boolean, default=False)
    nivel_auto = db.Column(db.Integer, default=0) # 0: Manual, 1: Python, 2: SQL, 3: JS
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)
class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(20), nullable=False) # 'Python', 'SQL', 'JavaScript'
    difficulty = db.Column(db.String(20), default='easy')
    question = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', 'D'
    hint = db.Column(db.Text)
def seed_quizzes():
    # Only seed if quizzes table is empty
    if Quiz.query.first() is not None:
        return
    quizzes_data = [
        # --- PYTHON QUIZZES ---
        {
            "language": "Python",
            "difficulty": "easy",
            "question": "¿Cuál es la función en Python para generar una secuencia de números y repetir una acción en un bucle 'for'?",
            "code_snippet": "for i in ______(5):\n    regar_cultivo(i)",
            "option_a": "loop",
            "option_b": "range",
            "option_c": "sequence",
            "option_d": "repeat",
            "correct_option": "B",
            "hint": "Genera números desde 0 hasta el límite indicado. Muy usada en bucles iterativos."
        },
        {
            "language": "Python",
            "difficulty": "easy",
            "question": "¿Cómo se define una condición para verificar si tenemos suficiente oro en Python?",
            "code_snippet": "______ oro >= 100:\n    comprar_semillas()",
            "option_a": "when",
            "option_b": "case",
            "option_c": "if",
            "option_d": "check",
            "correct_option": "C",
            "hint": "Es la palabra clave para bifurcaciones lógicas básicas."
        },
        {
            "language": "Python",
            "difficulty": "medium",
            "question": "¿Cómo se define una función para regar una parcela en Python?",
            "code_snippet": "______ regar_parcela(id):\n    print('Regando...')",
            "option_a": "func",
            "option_b": "function",
            "option_c": "def",
            "option_d": "define",
            "correct_option": "C",
            "hint": "Abreviatura de 'define' en Python."
        },
        {
            "language": "Python",
            "difficulty": "medium",
            "question": "¿Qué método se utiliza para añadir un nuevo vegetal a la lista de inventario en Python?",
            "code_snippet": "inventario = ['zanahoria']\ninventario.______('trigo')",
            "option_a": "add",
            "option_b": "push",
            "option_c": "append",
            "option_d": "insert",
            "correct_option": "C",
            "hint": "Este método agrega un elemento al final de una lista existente."
        },
        {
            "language": "Python",
            "difficulty": "hard",
            "question": "¿Cuál es la forma correcta de manejar un error al cosechar una planta inexistente?",
            "code_snippet": "______:\n    cosechar(parcela)\nexcept Exception as e:\n    print('Error!')",
            "option_a": "try",
            "option_b": "catch",
            "option_c": "attempt",
            "option_d": "safe",
            "correct_option": "A",
            "hint": "En Python, los bloques de excepciones usan 'try' y 'except'."
        },
        # --- SQL QUIZZES ---
        {
            "language": "SQL",
            "difficulty": "easy",
            "question": "¿Qué consulta se usa para obtener todas las parcelas de la base de datos?",
            "code_snippet": "______ * FROM parcelas;",
            "option_a": "GET",
            "option_b": "SELECT",
            "option_c": "SHOW",
            "option_d": "EXTRACT",
            "correct_option": "B",
            "hint": "Es la cláusula principal para realizar consultas en bases de datos relacionales."
        },
        {
            "language": "SQL",
            "difficulty": "easy",
            "question": "¿Cómo filtramos las parcelas de la granja que están automatizadas?",
            "code_snippet": "SELECT * FROM parcelas ______ automatizada = 1;",
            "option_a": "HAVING",
            "option_b": "WHEN",
            "option_c": "WHERE",
            "option_d": "FILTER",
            "correct_option": "C",
            "hint": "Se utiliza para filtrar registros basados en condiciones específicas."
        },
        {
            "language": "SQL",
            "difficulty": "medium",
            "question": "¿Qué instrucción SQL se usa para cambiar el estado de una parcela a 'ready'?",
            "code_snippet": "______ parcelas SET status = 'ready' WHERE id = 5;",
            "option_a": "CHANGE",
            "option_b": "SET",
            "option_c": "UPDATE",
            "option_d": "MODIFY",
            "correct_option": "C",
            "hint": "Modifica registros existentes en una tabla."
        },
        {
            "language": "SQL",
            "difficulty": "medium",
            "question": "¿Qué función agregada calcula la suma total del oro de todos los usuarios?",
            "code_snippet": "SELECT ______(gold) FROM usuarios;",
            "option_a": "TOTAL",
            "option_b": "ADD",
            "option_c": "SUM",
            "option_d": "COUNT",
            "correct_option": "C",
            "hint": "Suma los valores numéricos de una columna seleccionada."
        },
        {
            "language": "SQL",
            "difficulty": "hard",
            "question": "¿Cómo eliminamos los registros de parcelas muertas o secas?",
            "code_snippet": "______ FROM parcelas WHERE status = 'seca';",
            "option_a": "REMOVE",
            "option_b": "DROP",
            "option_c": "DELETE",
            "option_d": "CLEAR",
            "correct_option": "C",
            "hint": "Diferencia entre eliminar filas ('DELETE') y borrar la estructura de la tabla ('DROP')."
        },
        # --- JAVASCRIPT QUIZZES ---
        {
            "language": "JavaScript",
            "difficulty": "easy",
            "question": "¿Cómo declaramos una variable mutable para guardar el oro en JavaScript moderno?",
            "code_snippet": "______ oro = 0;",
            "option_a": "var",
            "option_b": "let",
            "option_c": "const",
            "option_d": "int",
            "correct_option": "B",
            "hint": "Reemplazó a 'var' en ES6 para declarar variables con ámbito de bloque."
        },
        {
            "language": "JavaScript",
            "difficulty": "easy",
            "question": "¿Qué función de ventana o temporizador ejecuta una función de riego repetidamente cada 2 segundos?",
            "code_snippet": "______(regar, 2000);",
            "option_a": "setTimeout",
            "option_b": "setInterval",
            "option_c": "runEvery",
            "option_d": "waitAndRun",
            "correct_option": "B",
            "hint": "Ejecuta de forma periódica e indefinida una función cada intervalo de milisegundos."
        },
        {
            "language": "JavaScript",
            "difficulty": "medium",
            "question": "¿Cuál es la sintaxis correcta para declarar una función flecha (arrow function) llamada regar?",
            "code_snippet": "const regar = ______ {\n    console.log('Riego JS');\n};",
            "option_a": "() ->",
            "option_b": "function()",
            "option_c": "() =>",
            "option_d": "=> ()",
            "correct_option": "C",
            "hint": "Se introdujo en ES6 y utiliza el operador 'flecha gorda'."
        },
        {
            "language": "JavaScript",
            "difficulty": "medium",
            "question": "¿Cómo seleccionamos el elemento HTML del contador de oro en el DOM?",
            "code_snippet": "const el = document.______('#txt-oro');",
            "option_a": "getElementById",
            "option_b": "find",
            "option_c": "querySelector",
            "option_d": "getElement",
            "correct_option": "C",
            "hint": "Selecciona el primer elemento que coincide con un selector CSS."
        },
        {
            "language": "JavaScript",
            "difficulty": "hard",
            "question": "¿Qué método de arreglos itera y transforma las parcelas en sus nuevos estados de crecimiento?",
            "code_snippet": "const nuevosEstados = parcelas.______(p => p.grow());",
            "option_a": "forEach",
            "option_b": "map",
            "option_c": "filter",
            "option_d": "reduce",
            "correct_option": "B",
            "hint": "Crea un nuevo array con los resultados de la llamada a la función indicada aplicados a cada elemento."
        }
    ]
    for q in quizzes_data:
        quiz = Quiz(
            language=q["language"],
            difficulty=q["difficulty"],
            question=q["question"],
            code_snippet=q["code_snippet"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_option=q["correct_option"],
            hint=q["hint"]
        )
        db.session.add(quiz)
    
    db.session.commit()
