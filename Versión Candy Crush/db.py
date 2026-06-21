import datetime
import json
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    gold = db.Column(db.Float, default=100.0)
    total_gold_earned = db.Column(db.Float, default=0.0)
    last_sync = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Sistema Cohesivo de Progresión Radical Python-Only
    xp = db.Column(db.Integer, default=0)              # 0 a 300 XP por nivel
    level = db.Column(db.Integer, default=1)           # Nivel 1, 2, 3 o 4
    unlocked_crops = db.Column(db.String(100), default='carrot') # Separados por coma, e.g. 'carrot,wheat'
    active_crop = db.Column(db.String(20), default='carrot')
    
    # Almacenamiento modular para Accesorios y Cuestionarios Completados (e.g., 'top_hat,q_1,q_2')
    bought_accessories = db.Column(db.String(200), default='') 
    equipped_accessory = db.Column(db.String(50), default='')
    frogs_count = db.Column(db.Integer, default=0)     # Ranitas Automatizadoras por Bloques

class Parcela(db.Model):
    __tablename__ = 'parcelas'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    plot_index = db.Column(db.Integer, nullable=False) # Índices estrictos del 0 al 63
    cultivo = db.Column(db.String(20), default='vacio') # 'vacio', 'dirt', 'carrot', 'wheat', 'pumpkin', 'watermelon'
    status = db.Column(db.String(20), default='idle')   # 'idle', 'growing', 'ready'
    grow_progress = db.Column(db.Float, default=0.0)   # Porcentaje de 0.0 a 100.0
    automatizada = db.Column(db.Boolean, default=False) # Administrado dinámicamente según frogs_count

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    difficulty = db.Column(db.String(20), nullable=False) # 'easy', 'medium', 'hard'
    question = db.Column(db.Text, nullable=False)
    code_snippet = db.Column(db.Text, default='')
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(2), nullable=False) # 'A', 'B', 'C' o 'D'
    hint = db.Column(db.Text, default='')
    
    # Arquitectura Estructurada en 3 Niveles / 15 Grupos Modulares
    quiz_group_id = db.Column(db.Integer, nullable=False) # ID del Grupo de Cuestionarios (1 al 15)
    step = db.Column(db.Integer, nullable=False, default=0) # Índice de pregunta consecutiva (0 a 2)

def seed_quizzes():
    """Siembra inicial y mapeo directo de las 45 preguntas reales de Python desde quizzes.json."""
    # Comprobar si la base de datos ya contiene exactamente las 45 preguntas del plan
    if Quiz.query.count() == 45:
        return
        
    # Limpiar de raíz cualquier residuo de mapeo de quizes corruptos o multilingües
    Quiz.query.delete()
    db.session.commit()
    
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quizzes.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                quizzes_data = json.load(f)
            
            for q in quizzes_data:
                quiz = Quiz(
                    difficulty=q.get('difficulty', 'easy'),
                    question=q['question'],
                    code_snippet=q.get('code_snippet', ''),
                    option_a=q['option_a'],
                    option_b=q['option_b'],
                    option_c=q['option_c'],
                    option_d=q['option_d'],
                    correct_option=q['correct_option'],
                    hint=q.get('hint', ''),
                    quiz_group_id=q['quiz_group_id'],
                    step=q['step']
                )
                db.session.add(quiz)
            
            db.session.commit()
            print("[DB SUCCESS] Los 15 Cuestionarios Estructurados (45 preguntas de Python) se han cargado con éxito.")
        except Exception as e:
            db.session.rollback()
            print(f"[DB ERROR] Error fatal durante el sembrado de quizzes.json: {e}")
    else:
        print(f"[DB WARNING] Archivo centralizado no encontrado en la ruta esperada: {json_path}")