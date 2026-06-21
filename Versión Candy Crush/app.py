import os
import datetime
import random
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from db import db, Usuario, Parcela, Quiz, seed_quizzes

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///code_and_crop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_db_initialized = False

# Inicialización y siembra obligatoria de la Base de Datos
@app.before_request
def initialize_db():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    db.create_all()
    seed_quizzes()

# Jugadores de IA simulados para el Leaderboard competitivo
AI_PLAYERS = [
    {"username": "MasterCoder 🥇", "base_gold": 15000, "base_level": 4},
    {"username": "CodeNinja 🥈", "base_gold": 8000, "base_level": 3},
    {"username": "NoobClipper 🥉", "base_gold": 500, "base_level": 1},
    {"username": "PyBoss 🐍", "base_gold": 25000, "base_level": 4},
]

# Configuración matemática estricta de cultivos (Tiempos en segundos y valores base)
CROP_GROWTH_TIMES = {
    'carrot': 8.0,
    'wheat': 20.0,
    'pumpkin': 50.0,
    'watermelon': 100.0
}

CROP_VALUES = {
    'carrot': 10.0,
    'wheat': 30.0,
    'pumpkin': 100.0,
    'watermelon': 350.0
}

ACCESSORY_MULTIPLIERS = {
    'top_hat': 1.1,
    'sunglasses': 1.3,
    'gold_crown': 1.8
}

# ============================================================================
# LÓGICA CORE: SINCRONIZACIÓN Y CRECIMIENTO PASIVO / AUTOMATIZACIÓN POR BLOQUES
# ============================================================================
def ensure_user_plots(user):
    """Garantiza que el usuario tenga creadas las 64 parcelas en la BD desde su inicio."""
    cantidad_actual = Parcela.query.filter_by(usuario_id=user.id).count()
    if cantidad_actual < 64:
        # Si faltan o es una cuenta desactualizada, purgar y reconstruir las 64 completas
        Parcela.query.filter_by(usuario_id=user.id).delete()
        for i in range(64):
            nueva_p = Parcela(usuario_id=user.id, plot_index=i, cultivo='vacio')
            db.session.add(nueva_p)
        db.session.commit()

def process_growth_sync(user):
    """Calcula el crecimiento pasivo y las ganancias automáticas de las ranitas por bloques."""
    now = datetime.datetime.utcnow()
    elapsed = (now - user.last_sync).total_seconds()
    user.last_sync = now
    
    if elapsed <= 0:
        return 0.0

    ensure_user_plots(user)
    plots = Parcela.query.filter_by(usuario_id=user.id).all()
    gold_gained = 0.0

    # Multiplicador cosmético global de las ranitas
    mult = ACCESSORY_MULTIPLIERS.get(user.equipped_accessory, 1.0)

    for p in plots:
        # Determinar si la parcela está automatizada por regla de bloques (1 Ranita = 4 parcelas)
        # Bloque 1 (Ranita 1): 0-3, Bloque 2 (Ranita 2): 4-7, etc.
        p.automatizada = (p.plot_index < user.frogs_count * 4)

        if p.cultivo == 'vacio' or p.cultivo == 'dirt':
            # Las ranitas automáticas siembran la semilla seleccionada si la parcela queda vacía/arada
            if p.automatizada and p.cultivo == 'dirt':
                p.cultivo = user.active_crop
                p.status = 'growing'
                p.grow_progress = 0.0
            continue

        if p.status == 'growing':
            total_time = CROP_GROWTH_TIMES.get(p.cultivo, 10.0)
            progress_increment = (elapsed / total_time) * 100.0
            p.grow_progress += progress_increment

            if p.grow_progress >= 100.0:
                p.grow_progress = 100.0
                p.status = 'ready'

        # Ciclo automático de cosecha y re-siembra pasiva por bloques de ranitas
        if p.status == 'ready' and p.automatizada:
            base_val = CROP_VALUES.get(p.cultivo, 0.0)
            gold_gained += base_val * mult
            
            # Re-siembra inmediata automatizada usando el cultivo activo
            p.cultivo = user.active_crop
            p.status = 'growing'
            p.grow_progress = 0.0

    user.gold += gold_gained
    user.total_gold_earned += gold_gained
    db.session.commit()
    return gold_gained

# ============================================================================
# RUTAS DE LA API DE CONTROL DE JUEGO
# ============================================================================
@app.route('/api/game/state', methods=['GET'])
def get_game_state():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "No autenticado"}), 401
        
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "Usuario inexistente"}), 404
        
    passive_gold = process_growth_sync(user)
    
    # Extraer los cuestionarios completados almacenados en el string comprado
    completed_quizzes = [int(x.replace('q_', '')) for x in user.bought_accessories.split(',') if x.startswith('q_')]
    
    # Límite visible exacto de parcelas según el plan por niveles
    max_plots_count = user.level * 16

    plots = Parcela.query.filter_by(usuario_id=user.id).order_by(Parcela.plot_index.asc()).all()
    plots_data = []
    for p in plots:
        plots_data.append({
            "plot_index": p.plot_index,
            "cultivo": p.cultivo,
            "status": p.status,
            "grow_progress": round(p.grow_progress, 1),
            "automatizada": (p.plot_index < user.frogs_count * 4)
        })

    return jsonify({
        "gold": round(user.gold, 2),
        "level": user.level,
        "xp": user.xp,
        "unlocked_crops": user.unlocked_crops.split(','),
        "active_crop": user.active_crop,
        "equipped_accessory": user.equipped_accessory,
        "frogs_count": user.frogs_count,
        "max_frogs": user.level * 4,
        "max_plots": max_plots_count,
        "plots": plots_data,
        "completed_quizzes": completed_quizzes,
        "passive_gold_gained": round(passive_gold, 2)
    })

@app.route('/api/game/click', methods=['POST'])
def handle_click():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "No autenticado"}), 401
        
    user = Usuario.query.get(user_id)
    data = request.get_json() or {}
    plot_index = data.get('plot_index')
    action = data.get('action') # 'click' (arar), 'plant', 'harvest'

    if plot_index is None or plot_index >= (user.level * 16):
        return jsonify({"status": "error", "message": "Parcela bloqueada o inválida"}), 400

    # Sincronizar crecimiento antes de aplicar la acción manual
    process_growth_sync(user)
    
    p = Parcela.query.filter_by(usuario_id=user.id, plot_index=plot_index).first()
    if not p:
        return jsonify({"status": "error", "message": "Parcela no encontrada"}), 404

    gold_gained = 0.0

    if action == 'click' and p.cultivo == 'vacio':
        p.cultivo = 'dirt'
        p.status = 'idle'
        p.grow_progress = 0.0
    elif action == 'plant' and p.cultivo == 'dirt':
        p.cultivo = user.active_crop
        p.status = 'growing'
        p.grow_progress = 0.0
    elif action == 'harvest' and p.status == 'ready':
        base_val = CROP_VALUES.get(p.cultivo, 0.0)
        mult = ACCESSORY_MULTIPLIERS.get(user.equipped_accessory, 1.0)
        gold_gained = base_val * mult
        
        user.gold += gold_gained
        user.total_gold_earned += gold_gained
        
        p.cultivo = 'dirt'
        p.status = 'idle'
        p.grow_progress = 0.0
    else:
        return jsonify({"status": "error", "message": "Acción manual no válida en el estado actual"}), 400

    db.session.commit()
    return jsonify({"status": "success", "gold_gained": round(gold_gained, 2)})

# ============================================================================
# API DE CUESTIONARIOS ESTRUCTURADOS DE PYTHON (45 PREGUNTAS REALES)
# ============================================================================
@app.route('/api/game/quizzes', methods=['GET'])
def get_quiz_question():
    if not session.get('user_id'):
        return jsonify({"status": "error", "message": "No autenticado"}), 401
        
    group_id = request.args.get('group_id', type=int)
    step = request.args.get('step', type=int)

    if not group_id or step is None:
        return jsonify({"status": "error", "message": "Parámetros incompletos"}), 400

    quiz = Quiz.query.filter_by(quiz_group_id=group_id, step=step).first()
    if not quiz:
        return jsonify({"status": "error", "message": "Pregunta de Python no encontrada"}), 404

    return jsonify({
        "question": quiz.question,
        "code_snippet": quiz.code_snippet,
        "option_a": quiz.option_a,
        "option_b": quiz.option_b,
        "option_c": quiz.option_c,
        "option_d": quiz.option_d,
        "hint": quiz.hint
    })

@app.route('/api/game/answer', methods=['POST'])
def submit_answer():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "No autenticado"}), 401
        
    user = Usuario.query.get(user_id)
    data = request.get_json() or {}
    group_id = data.get('group_id')
    step = data.get('step')
    selected_option = data.get('option')

    quiz = Quiz.query.filter_by(quiz_group_id=group_id, step=step).first()
    if not quiz:
        return jsonify({"status": "error", "message": "Pregunta no encontrada"}), 404

    is_correct = (selected_option == quiz.correct_option)

    if is_correct:
        if step == 2:
            # Recompensas fijas del Plan de Implementación al terminar el paso 3 (índice 2)
            user.xp += 100
            user.gold += 500
            
            # Guardado persistente del grupo de cuestionario completado
            current_completed = [x for x in user.bought_accessories.split(',') if x]
            quiz_marker = f"q_{group_id}"
            if quiz_marker not in current_completed:
                current_completed.append(quiz_marker)
                user.bought_accessories = ','.join(current_completed)

            # Sistema de subida de nivel dinámica al alcanzar 300 XP
            if user.xp >= 300:
                user.level = min(4, user.level + 1)
                user.xp -= 300
                
                # Desbloqueo automático de cultivos en la tienda según nivel
                crops_by_level = {2: 'wheat', 3: 'pumpkin', 4: 'watermelon'}
                current_crops = user.unlocked_crops.split(',')
                new_crop = crops_by_level.get(user.level)
                if new_crop and new_crop not in current_crops:
                    current_crops.append(new_crop)
                    user.unlocked_crops = ','.join(current_crops)
            
            db.session.commit()
            return jsonify({
                "status": "success",
                "correct": True,
                "completed": True,
                "message": "¡Excelente! Cuestionario completado con éxito. Recompensa: +100 XP y +500 🪙."
            })
        else:
            return jsonify({
                "status": "success",
                "correct": True,
                "completed": False,
                "message": f"¡Correcto! Avanzando al paso {step + 2}/3 del cuestionario."
            })
    else:
        return jsonify({
            "status": "success",
            "correct": False,
            "completed": True,
            "message": f"Respuesta incorrecta en el paso {step + 1}. El cuestionario ha sido cancelado. ¡Estudia la pista e inténtalo de nuevo desde el paso 1!"
        })

# ============================================================================
# RUTAS DE ADQUISICIÓN DE TIENDA Y CONFIGURACIONES
# ============================================================================
@app.route('/api/game/select_crop', methods=['POST'])
def select_crop():
    user_id = session.get('user_id')
    user = Usuario.query.get(user_id)
    data = request.get_json() or {}
    crop = data.get('crop')
    
    if crop in user.unlocked_crops.split(','):
        user.active_crop = crop
        db.session.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Cultivo no desbloqueado"}), 400

@app.route('/api/game/buy_license', methods=['POST'])
def buy_license():
    user_id = session.get('user_id')
    user = Usuario.query.get(user_id)
    data = request.get_json() or {}
    crop = data.get('crop')

    prices = {'wheat': 500, 'pumpkin': 2000, 'watermelon': 6000}
    levels = {'wheat': 2, 'pumpkin': 3, 'watermelon': 4}

    if crop not in prices:
        return jsonify({"status": "error", "message": "Cultivo inválido"}), 400

    current_crops = user.unlocked_crops.split(',')
    if crop in current_crops:
        return jsonify({"status": "error", "message": "Ya tienes esta licencia"}), 400

    if user.level < levels[crop]:
        return jsonify({"status": "error", "message": f"Requiere nivel {levels[crop]} para adquirir"}), 400

    cost = prices[crop]
    if user.gold < cost:
        return jsonify({"status": "error", "message": "Oro insuficiente"}), 400

    user.gold -= cost
    current_crops.append(crop)
    user.unlocked_crops = ','.join(current_crops)
    db.session.commit()
    return jsonify({"status": "success", "message": f"¡Licencia de {crop.capitalize()} comprada con éxito!"})

@app.route('/api/game/buy_frog', methods=['POST'])
def buy_frog():
    user_id = session.get('user_id')
    user = Usuario.query.get(user_id)
    
    max_frogs_allowed = user.level * 4
    if user.frogs_count >= max_frogs_allowed:
        return jsonify({"status": "error", "message": f"Límite alcanzado. Máximo {max_frogs_allowed} ranitas para tu nivel actual"}), 400

    if user.gold < 1500:
        return jsonify({"status": "error", "message": "Oro insuficiente (Cuesta 1,500 🪙)"}), 400

    user.gold -= 1500
    user.frogs_count += 1
    db.session.commit()
    return jsonify({"status": "success", "message": f"¡Ranita comprada! Automatiza un nuevo bloque completo de 4 parcelas."})

@app.route('/api/game/buy_accessory', methods=['POST'])
def buy_accessory():
    user_id = session.get('user_id')
    user = Usuario.query.get(user_id)
    data = request.get_json() or {}
    acc = data.get('accessory')

    prices = {'top_hat': 400, 'sunglasses': 1200, 'gold_crown': 4500}
    if acc not in prices:
        return jsonify({"status": "error", "message": "Accesorio inválido"}), 400

    if user.gold < prices[acc]:
        return jsonify({"status": "error", "message": "Oro insuficiente"}), 400

    user.gold -= prices[acc]
    user.equipped_accessory = acc
    db.session.commit()
    return jsonify({"status": "success", "message": f"¡Accesorio equipado! Multiplicador global de ranitas activo."})

# --- SISTEMA ESTRICTO DE DESHABILITACIÓN DE CACHÉ ---
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# --- AUTENTICACIÓN Y VISTAS BASE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            user = Usuario.query.filter_by(username=username).first()
            if not user:
                user = Usuario(username=username, password_hash='dummy')
                db.session.add(user)
                db.session.commit()
            session['user_id'] = user.id
            ensure_user_plots(user)
            return redirect(url_for('home'))
    return '''
        <body style="background:#14110f;color:#f3f4f6;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;">
            <form method="post" style="background:#221a14;padding:30px;border-radius:15px;border:3px solid #ea580c;text-align:center;">
                <h2 style="color:#ea580c;margin-bottom:20px;">CODE & CROP: LOGIN</h2>
                <input type="text" name="username" placeholder="Tu Nombre de Usuario" required style="padding:10px;border-radius:8px;border:1px solid #3d3025;background:#14110f;color:white;margin-bottom:15px;width:200px;"><br>
                <button type="submit" style="background:#ea580c;color:white;border:none;padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;">Entrar a la Granja</button>
            </form>
        </body>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/api/game/leaderboard', methods=['GET'])
def get_leaderboard():
    user_id = session.get('user_id')
    real_users = Usuario.query.order_by(Usuario.gold.desc()).limit(10).all()
    leaderboard = []
    for u in real_users:
        leaderboard.append({
            "username": f"✨ {u.username} (Tú)" if u.id == user_id else u.username,
            "gold": round(u.gold, 1),
            "level": u.level,
            "is_ai": False
        })
    for ai in AI_PLAYERS:
        leaderboard.append({"username": ai["username"], "gold": ai["base_gold"], "level": ai["base_level"], "is_ai": True})
    leaderboard.sort(key=lambda x: x["gold"], reverse=True)
    return jsonify(leaderboard[:8])

if __name__ == '__main__':
    app.run(debug=True, port=5000)