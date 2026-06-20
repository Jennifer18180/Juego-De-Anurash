from flask import Flask, jsonify, request, render_template
from models import db, Usuario, Parcela
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///anurash.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- 🐱 BANCO DE CONOCIMIENTO DEL GATITO VIAJERO ---
DATOS_GATITO = [
    {"tema": "Bucles For", "consejo": "Un bucle 'for' repite una acción por cada elemento en un rango. ¡Es el secreto de las ranitas regadoras!"},
    {"tema": "Condicionales If", "consejo": "Usa 'if' para tomar decisiones. Si hay sequía, riega; si no, ahorra agua."},
    {"tema": "Variables", "consejo": "Las variables guardan información, como contenedores. Tu contador de oro es una gran variable variable."}
]

# --- 🦉 BANCO DE QUIZES ESTILO DUOLINGO ---
# Guardamos las plantillas de respuestas correctas de forma segura en el backend
QUIZES = {
    "bucle_for": {
        "pregunta": "Completa el código para que la ranita repita el riego 5 veces:",
        "codigo_incompleto": "for i in ______(5):",
        "opciones": ["loop", "range", "list"],
        "correcta": "range"
    }
}

# Crear la base de datos la primera vez
@app.before_request
def inicializar_juego():
    db.create_all()

# --- 🚀 RUTAS DEL JUEGO ---

@app.route('/game/turno', methods=['POST'])
def avanzar_turno():
    data = request.json
    usuario = Usuario.query.get(data['usuario_id'])
    
    # SOLUCIÓN AL BUG: Si es la primera vez que abres el juego, creamos al jugador de prueba
    if not usuario:
        usuario = Usuario(id=1, username="PyFarmer99", oro=1200, porcentaje_auto=0)
        db.session.add(usuario)
        db.session.commit()
        
    # Calcular ingresos automáticos de las parcelas
    parcelas_auto = Parcela.query.filter_by(usuario_id=usuario.id, automatizada=True).count()
    
    # Cada clic manual da +1 si la parcela no está automatizada
    oro_ganado = (parcelas_auto * 20) + 1
    usuario.oro += oro_ganado
    db.session.commit()
    
    return jsonify({
        "oro_total": usuario.oro,
        "oro_ganado_pasivo": parcelas_auto * 20,
        "porcentaje_auto": usuario.porcentaje_auto
    })

@app.route('/game/gatito', methods=['GET'])
def aparecer_gatito():
    """ Selecciona un dato curioso aleatorio para el jugador """
    dato = random.choice(DATOS_GATITO)
    return jsonify({
        "evento": "¡El Gatito Viajero ha llegado!",
        "tema": dato["tema"],
        "consejo": dato["consejo"]
    })

@app.route('/game/quiz/validar', methods=['POST'])
def validar_duolingo():
    """ Validador estilo Duolingo sin exponer la respuesta al Frontend """
    data = request.json # Recibe { usuario_id, quiz_id, opcion_seleccionada, p_x, p_y }
    
    quiz = QUIZES.get(data['quiz_id'])
    if not quiz:
        return jsonify({"status": "error", "mensaje": "Quiz no válido"}), 400
        
    # Validación limpia estilo Duolingo
    if data['opcion_seleccionada'] == quiz['correcta']:
        # Modificar parcela a Automatizada (Transacción SQL segura)
        parcela = Parcela.query.filter_by(
            usuario_id=data['usuario_id'], 
            posicion_x=data['p_x'], 
            posicion_y=data['p_y']
        ).first()
        
        if parcela:
            parcela.automatizada = True
            
            # Recalcular % de automatización del usuario
            usuario = Usuario.query.get(data['usuario_id'])
            total_parcelas = Parcela.query.filter_by(usuario_id=usuario.id).count() or 64
            auto_parcelas = Parcela.query.filter_by(usuario_id=usuario.id, automatizada=True).count()
            usuario.porcentaje_auto = int((auto_parcelas / total_parcelas) * 100)
            
            db.session.commit()
            
        return jsonify({
            "status": "correcto", 
            "mensaje": "¡Excelente! La ranita ha tomado el control de la parcela.",
            "porcentaje_auto": usuario.porcentaje_auto
        })
    else:
        return jsonify({
            "status": "incorrecto", 
            "mensaje": "¡Oh no! Inténtalo de nuevo. El gatico sigue trabajando manualmente."
        })

# --- 🏠 RUTA PRINCIPAL: CARGA EL JUEGO VISUAL ---
@app.route('/')
def home():
    # Esto busca automáticamente el archivo index.html dentro de la carpeta 'templates'
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)