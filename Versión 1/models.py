from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    oro = db.Column(db.Integer, default=0)
    porcentaje_auto = db.Column(db.Integer, default=0)
    # Relación para acceder a las parcelas del usuario de golpe
    parcelas = db.relationship('Parcela', backref='dueno', lazy=True)

class Parcela(db.Model):
    __tablename__ = 'parcelas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    posicion_x = db.Column(db.Integer, nullable=False)
    posicion_y = db.Column(db.Integer, nullable=False)
    cultivo = db.Column(db.String(20), default='vacio') # 'zanahoria', 'trigo', etc.
    automatizada = db.Column(db.Boolean, default=False) # False = Gatico, True = Ranita