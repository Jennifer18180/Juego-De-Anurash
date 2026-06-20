import os
import datetime
import random
import webbrowser
from threading import Timer
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from db import db, Usuario, Parcela, Quiz, seed_quizzes
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///code_and_crop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
_db_initialized = False
# Seed database on first request
@app.before_request
def initialize_db():
    global _db_initialized
    if _db_initialized:
        return
    _db_initialized = True
    db.create_all()
    # Migrate: add plot_index column if it doesn't exist (for existing DBs)
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE parcelas ADD COLUMN plot_index INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
    except Exception:
        pass  # Column already exists — ignore
    # Repair: recompute plot_index from grid position for rows where it's still 0
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text(
                "UPDATE parcelas SET plot_index = (posicion_x * 8 + posicion_y) "
                "WHERE plot_index = 0 AND NOT (posicion_x = 0 AND posicion_y = 0)"
            ))
            conn.commit()
    except Exception:
        pass
    seed_quizzes()
# Simulated AI players for a live competitive leaderboard
AI_PLAYERS = [
    {"username": "MasterCoder 🥇", "base_gold": 15000, "base_auto": 92, "grow_rate_gold": 5.0, "grow_rate_auto": 0.05},
    {"username": "CodeNinja 🥈", "base_gold": 8000, "base_auto": 78, "grow_rate_gold": 3.0, "grow_rate_auto": 0.08},
    {"username": "NoobClipper 🥉", "base_gold": 500, "base_auto": 5, "grow_rate_gold": 0.5, "grow_rate_auto": 0.1},
    {"username": "PyBoss 🐍", "base_gold": 25000, "base_auto": 100, "grow_rate_gold": 12.0, "grow_rate_auto": 0.0},
]
START_TIME = datetime.datetime.utcnow()
def get_live_ai_leaderboard():
    elapsed = (datetime.datetime.utcnow() - START_TIME).total_seconds()
    leaderboard = []
    for ai in AI_PLAYERS:
        current_gold = ai["base_gold"] + (elapsed * ai["grow_rate_gold"])
        current_auto = min(100.0, ai["base_auto"] + (elapsed * ai["grow_rate_auto"]))
        leaderboard.append({
            "username": ai["username"],
            "gold": round(current_gold, 1),
            "porcentaje_auto": round(current_auto, 1),
            "is_ai": True
        })
    return leaderboard
# Tip database
DATOS_GATITO = [
    {"tema": "Bucles For", "consejo": "Un bucle 'for' repite una acción en un rango. ¡Es el secreto de las ranitas regadoras!"},
    {"tema": "Condicionales If", "consejo": "Usa 'if' para tomar decisiones. Si hay sequía, riega; de lo contrario, ahorra agua."},
    {"tema": "Variables", "consejo": "Las variables guardan información. Tu saldo de oro es una variable que crece con tus cosechas."},
    {"tema": "Consultas SQL", "consejo": "SQL usa SELECT para extraer datos y UPDATE para cambiarlos. ¡Las bases de datos ordenan tu granja!"},
    {"tema": "Promesas en JS", "consejo": "Una promesa en JavaScript representa un valor que estará disponible en el futuro, como una planta creciendo."},
    {"tema": "Transacciones", "consejo": "Las transacciones SQL aseguran que dos operaciones ocurran juntas o ninguna ocurra. ¡Evita hackeos!"}
]
def ensure_user_plots(user):
    # Check if user has 64 plots (indexes 0 to 63)
    existing_count = Parcela.query.filter_by(usuario_id=user.id).count()
    if existing_count < 64:
        # Get existing indexes
        existing_plots = Parcela.query.filter_by(usuario_id=user.id).all()
        existing_indices = {p.plot_index for p in existing_plots}
        
        # Batch insert missing plots
        now = datetime.datetime.utcnow()
        new_plots = []
        for i in range(64):
            if i not in existing_indices:
                new_plots.append(Parcela(
                    usuario_id=user.id,
                    plot_index=i,
                    posicion_x=i // 8,
                    posicion_y=i % 8,
                    cultivo='vacio',
                    status='empty',
                    grow_progress=0.0,
                    automatizada=False,
                    nivel_auto=0,
                    last_updated=now
                ))
        if new_plots:
            db.session.add_all(new_plots)
            db.session.commit()
# --- AUTHENTICATION ROUTES ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Nombre de usuario y contraseña requeridos"}), 400
        
    if Usuario.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "El usuario ya existe"}), 400
        
    try:
        user = Usuario(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Create plots
        ensure_user_plots(user)
        
        session['user_id'] = user.id
        return jsonify({"status": "success", "message": "Usuario registrado exitosamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error al registrar el usuario"}), 500
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    user = Usuario.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        ensure_user_plots(user)
        return jsonify({"status": "success", "message": "Inicio de sesión correcto"})
    else:
        return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401
@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"status": "success"})
@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    user_id = session.get('user_id')
    if not user_id:
        # Auto-login a default user for local playing / quick testing convenience
        default_user = Usuario.query.filter_by(username='PyFarmer99').first()
        if not default_user:
            default_user = Usuario(username='PyFarmer99')
            default_user.set_password('admin123')
            db.session.add(default_user)
            db.session.commit()
            ensure_user_plots(default_user)
        session['user_id'] = default_user.id
        user_id = default_user.id
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({"logged_in": False})
        
    return jsonify({
        "logged_in": True,
        "username": user.username,
        "gold": round(user.gold, 2),
        "prestige_count": user.prestige_count,
        "active_language": user.active_language
    })
# --- GAME SYSTEM ROUTES ---
def process_growth_sync(user):
    now = datetime.datetime.utcnow()
    # Time delta
    elapsed = (now - user.last_sync).total_seconds()
    if elapsed <= 0:
        return 0.0
    total_passive_gold = 0.0
    plots = Parcela.query.filter_by(usuario_id=user.id).all()
    
    # Growth configuration
    # Carrot: 8s growth time. Wheat: 20s. Pumpkin: 50s.
    growth_times = {
        'vacio': 1.0,
        'carrot': 8.0,
        'wheat': 20.0,
        'pumpkin': 50.0
    }
    
    # Yield values
    crop_values = {
        'carrot': 10.0,
        'wheat': 30.0,
        'pumpkin': 100.0
    }
    # Prestige Multipliers
    # Python: 1x, SQL: 10x, JS: 100x
    multipliers = {
        'Python': 1.0,
        'SQL': 10.0,
        'JavaScript': 100.0
    }
    mult = multipliers.get(user.active_language, 1.0)
    for p in plots:
        if p.automatizada:
            # Automated frogs continuously grow, harvest, and replant carrots (or their current crop)
            crop = p.cultivo if p.cultivo in crop_values else 'carrot'
            p.cultivo = crop  # ensure it's not empty
            
            grow_time = growth_times.get(crop, 8.0)
            crop_val = crop_values.get(crop, 10.0)
            
            # Calculate cycles completed since last sync
            # Start from current progress
            starting_progress_seconds = (p.grow_progress / 100.0) * grow_time
            total_time_avail = starting_progress_seconds + elapsed
            
            cycles = int(total_time_avail // grow_time)
            rem_seconds = total_time_avail % grow_time
            
            if cycles > 0:
                gold_earned = cycles * crop_val * mult
                total_passive_gold += gold_earned
                p.grow_progress = (rem_seconds / grow_time) * 100.0
                p.status = 'growing'
            else:
                p.grow_progress = (total_time_avail / grow_time) * 100.0
                p.status = 'growing' if p.grow_progress < 100.0 else 'ready'
                
            p.last_updated = now
        else:
            # Manual crops just grow up to 100% and wait for harvest
            if p.status == 'growing' and p.cultivo in growth_times:
                grow_time = growth_times.get(p.cultivo, 8.0)
                progress_gain = (elapsed / grow_time) * 100.0
                p.grow_progress = min(100.0, p.grow_progress + progress_gain)
                if p.grow_progress >= 100.0:
                    p.status = 'ready'
                p.last_updated = now
    user.gold += total_passive_gold
    user.total_gold_earned += total_passive_gold
    user.last_sync = now
    db.session.commit()
    
    return total_passive_gold
@app.route('/api/game/state', methods=['GET'])
def game_state():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Inicie sesión primero"}), 401
        
    user = Usuario.query.get(user_id)
    ensure_user_plots(user)
    
    # Process passive gains
    passive_earned = process_growth_sync(user)
    
    plots = Parcela.query.filter_by(usuario_id=user.id).order_by(Parcela.plot_index).all()
    plots_data = []
    auto_count = 0
    
    for p in plots:
        if p.automatizada:
            auto_count += 1
        plots_data.append({
            "plot_index": p.plot_index,
            "posicion_x": p.posicion_x,
            "posicion_y": p.posicion_y,
            "cultivo": p.cultivo,
            "status": p.status,
            "grow_progress": round(p.grow_progress, 1),
            "automatizada": p.automatizada,
            "nivel_auto": p.nivel_auto
        })
        
    porcentaje_auto = int((auto_count / 64) * 100) if 64 > 0 else 0
    
    return jsonify({
        "username": user.username,
        "gold": round(user.gold, 2),
        "prestige_count": user.prestige_count,
        "active_language": user.active_language,
        "porcentaje_auto": porcentaje_auto,
        "auto_count": auto_count,
        "passive_earned": round(passive_earned, 2),
        "plots": plots_data
    })
@app.route('/api/game/click', methods=['POST'])
def click_plot():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Inicie sesión"}), 401
        
    user = Usuario.query.get(user_id)
    data = request.json or {}
    plot_index = data.get('plot_index')
    action = data.get('action') # 'click' (manual gold), 'plant', 'harvest'
    crop_type = data.get('crop_type', 'carrot') # 'carrot', 'wheat', 'pumpkin'
    if plot_index is None:
        return jsonify({"status": "error", "message": "Index de parcela faltante"}), 400
    p = Parcela.query.filter_by(usuario_id=user.id, plot_index=plot_index).first()
    if not p:
        return jsonify({"status": "error", "message": "Parcela no encontrada"}), 404
    # Sync passive gains first so we don't overwrite timelines
    process_growth_sync(user)
    now = datetime.datetime.utcnow()
    gold_gained = 0.0
    gold_spent = 0.0
    # Seed Costs
    seed_costs = {'carrot': 5.0, 'wheat': 15.0, 'pumpkin': 50.0}
    # Direct click values
    crop_values = {'carrot': 10.0, 'wheat': 30.0, 'pumpkin': 100.0}
    
    multipliers = {'Python': 1.0, 'SQL': 10.0, 'JavaScript': 100.0}
    mult = multipliers.get(user.active_language, 1.0)
    try:
        if action == 'click':
            # Plowing grass to soil (first click on empty plot)
            if p.cultivo == 'vacio' and p.status == 'empty':
                p.cultivo = 'dirt'
                gold_gained = 1.0 * mult
                user.gold += gold_gained
                user.total_gold_earned += gold_gained
                p.last_updated = now
            # Click on growing crop (manual gold tapping)
            elif p.status == 'growing' and not p.automatizada:
                gold_gained = 1.0 * mult
                user.gold += gold_gained
                user.total_gold_earned += gold_gained
                p.last_updated = now
            # Click on dirt (also give a coin)
            elif p.cultivo == 'dirt':
                gold_gained = 0.5 * mult
                user.gold += gold_gained
                user.total_gold_earned += gold_gained
                p.last_updated = now
        elif action == 'plant':
            # Can only plant on tilled soil (dirt)
            if p.cultivo == 'dirt' and not p.automatizada:
                cost = seed_costs.get(crop_type, 5.0) * mult
                if user.gold >= cost:
                    user.gold -= cost
                    p.cultivo = crop_type
                    p.status = 'growing'
                    p.grow_progress = 0.0
                    p.last_updated = now
                    gold_spent = cost
                else:
                    return jsonify({"status": "error", "message": "Oro insuficiente para comprar semillas"}), 400
            else:
                return jsonify({"status": "error", "message": "Debes arar la parcela antes de plantar"}), 400
        elif action == 'harvest':
            if p.status == 'ready' and not p.automatizada:
                val = crop_values.get(p.cultivo, 10.0) * mult
                gold_gained = val
                user.gold += gold_gained
                user.total_gold_earned += gold_gained
                p.cultivo = 'vacio'
                p.status = 'empty'
                p.grow_progress = 0.0
                p.last_updated = now
            else:
                return jsonify({"status": "error", "message": "El cultivo no está listo o es automático"}), 400
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({
        "status": "success",
        "gold": round(user.gold, 2),
        "gold_gained": round(gold_gained, 2),
        "gold_spent": round(gold_spent, 2),
        "plot": {
            "plot_index": p.plot_index,
            "cultivo": p.cultivo,
            "status": p.status,
            "grow_progress": round(p.grow_progress, 1),
            "automatizada": p.automatizada
        }
    })
# --- QUIZ & CHALLENGE SYSTEM (3 QUESTIONS) ---
@app.route('/api/game/challenge/start', methods=['POST'])
def start_challenge():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Inicie sesión"}), 401
        
    user = Usuario.query.get(user_id)
    data = request.json or {}
    plot_index = data.get('plot_index')
    if plot_index is None:
        return jsonify({"status": "error", "message": "Índice de parcela faltante"}), 400
    # Retrieve 3 random quizzes for the active language
    quizzes = Quiz.query.filter_by(language=user.active_language).all()
    if not quizzes:
        return jsonify({"status": "error", "message": "No hay quizes disponibles"}), 404
        
    if len(quizzes) < 3:
        # duplicate list to ensure we have 3 questions if quiz bank is small
        quizzes = quizzes * 3
    selected_quizzes = random.sample(quizzes, 3)
    # Save to session
    session['challenge_plot'] = plot_index
    session['challenge_questions'] = [q.id for q in selected_quizzes]
    session['challenge_step'] = 0
    first_quiz = selected_quizzes[0]
    return jsonify({
        "status": "success",
        "step": 0,
        "total_steps": 3,
        "quiz": {
            "quiz_id": first_quiz.id,
            "language": first_quiz.language,
            "difficulty": first_quiz.difficulty,
            "question": first_quiz.question,
            "code_snippet": first_quiz.code_snippet,
            "options": [first_quiz.option_a, first_quiz.option_b, first_quiz.option_c, first_quiz.option_d],
            "hint": first_quiz.hint
        }
    })
@app.route('/api/game/challenge/submit', methods=['POST'])
def submit_challenge_answer():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Inicie sesión"}), 401
        
    user = Usuario.query.get(user_id)
    data = request.json or {}
    selected_option_index = data.get('selected_option_index')
    challenge_plot = session.get('challenge_plot')
    challenge_questions = session.get('challenge_questions')
    challenge_step = session.get('challenge_step')
    if selected_option_index is None or challenge_plot is None or challenge_questions is None or challenge_step is None:
        return jsonify({"status": "error", "message": "Desafío no iniciado o sesión expirada"}), 400
    current_quiz_id = challenge_questions[challenge_step]
    quiz = Quiz.query.get(current_quiz_id)
    if not quiz:
        return jsonify({"status": "error", "message": "Pregunta no encontrada"}), 404
    option_mapping = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
    user_option = option_mapping.get(selected_option_index)
    if user_option == quiz.correct_option:
        next_step = challenge_step + 1
        session['challenge_step'] = next_step
        if next_step < 3:
            # Send next question
            next_quiz_id = challenge_questions[next_step]
            next_quiz = Quiz.query.get(next_quiz_id)
            return jsonify({
                "status": "success",
                "correct": True,
                "completed": False,
                "step": next_step,
                "total_steps": 3,
                "quiz": {
                    "quiz_id": next_quiz.id,
                    "language": next_quiz.language,
                    "difficulty": next_quiz.difficulty,
                    "question": next_quiz.question,
                    "code_snippet": next_quiz.code_snippet,
                    "options": [next_quiz.option_a, next_quiz.option_b, next_quiz.option_c, next_quiz.option_d],
                    "hint": next_quiz.hint
                }
            })
        else:
            # Completed all 3! Automate
            p = Parcela.query.filter_by(usuario_id=user.id, plot_index=challenge_plot).first()
            if p:
                p.automatizada = True
                p.nivel_auto = 1 if user.active_language == 'Python' else (2 if user.active_language == 'SQL' else 3)
                p.status = 'growing'
                p.grow_progress = 0.0
                p.last_updated = datetime.datetime.utcnow()
                
                # Recalculate percentage
                auto_count = Parcela.query.filter_by(usuario_id=user.id, automatizada=True).count()
                porcentaje_auto = int((auto_count / 64) * 100)
                
                db.session.commit()
                
                # Clear session
                session.pop('challenge_plot', None)
                session.pop('challenge_questions', None)
                session.pop('challenge_step', None)
                return jsonify({
                    "status": "success",
                    "correct": True,
                    "completed": True,
                    "message": "¡Felicidades! Has completado el desafío de 3 preguntas con éxito. ¡La ranita ahora automatiza esta parcela!",
                    "porcentaje_auto": porcentaje_auto,
                    "plot_index": challenge_plot
                })
    else:
        # Wrong answer, clear session
        session.pop('challenge_plot', None)
        session.pop('challenge_questions', None)
        session.pop('challenge_step', None)
        return jsonify({
            "status": "success",
            "correct": False,
            "completed": True,
            "message": f"Respuesta incorrecta. Has fallado en la pregunta {challenge_step + 1}. El gatico sigue trabajando manualmente y el globo aerostático se ha ido."
        })
# --- SHOP & PRESTIGE RESET ---
@app.route('/api/game/shop/buy_language', methods=['POST'])
def buy_language():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Inicie sesión"}), 401
        
    user = Usuario.query.get(user_id)
    data = request.json or {}
    target_language = data.get('language') # 'SQL', 'JavaScript'
    costs = {
        'SQL': 5000.0,
        'JavaScript': 10000.0
    }
    if target_language not in costs:
        return jsonify({"status": "error", "message": "Lenguaje no válido"}), 400
    cost = costs[target_language]
    if user.gold < cost:
        return jsonify({"status": "error", "message": "Oro insuficiente para comprar esta licencia"}), 400
    # SQL Atomic Transaction: Prestige Reset
    try:
        user.gold -= cost
        user.active_language = target_language
        user.prestige_count += 1
        
        # Reset all plots to default (manual, empty)
        plots = Parcela.query.filter_by(usuario_id=user.id).all()
        now = datetime.datetime.utcnow()
        for p in plots:
            p.cultivo = 'vacio'
            p.status = 'empty'
            p.grow_progress = 0.0
            p.automatizada = False
            p.nivel_auto = 0
            p.last_updated = now
            
        user.last_sync = now
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": f"¡Módulo {target_language} desbloqueado! Tu granja se ha vendido al Banco Central. ¡Nuevos multiplicadores activos!",
            "gold": round(user.gold, 2),
            "active_language": user.active_language,
            "prestige_count": user.prestige_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
# --- LEADERBOARD & GATITO TIPS ---
@app.route('/api/game/leaderboard', methods=['GET'])
def get_leaderboard():
    user_id = session.get('user_id')
    
    # 1. Fetch real players
    real_users = Usuario.query.order_by(Usuario.gold.desc()).limit(10).all()
    leaderboard = []
    
    for u in real_users:
        # Calculate auto percentage
        auto_count = Parcela.query.filter_by(usuario_id=u.id, automatizada=True).count()
        porcentaje_auto = int((auto_count / 64) * 100) if 64 > 0 else 0
        leaderboard.append({
            "username": f"✨ {u.username} (Tú)" if u.id == user_id else u.username,
            "gold": round(u.gold, 1),
            "porcentaje_auto": porcentaje_auto,
            "is_ai": False
        })
        
    # 2. Fetch AI players
    ai_list = get_live_ai_leaderboard()
    leaderboard.extend(ai_list)
    
    # 3. Sort merged list
    leaderboard.sort(key=lambda x: x["gold"], reverse=True)
    
    return jsonify(leaderboard[:8]) # Top 8 combined
@app.route('/api/game/gatito', methods=['GET'])
def get_gatito_tip():
    tip = random.choice(DATOS_GATITO)
    return jsonify(tip)
# --- HOME ENTRY ---
@app.route('/')
def home():
    return render_template('index.html')
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")
if __name__ == '__main__':
    # Only open browser on the main reload thread or in non-debug mode
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(1.5, open_browser).start()
    app.run(debug=True, port=5000)
