import unittest
import json
import datetime
from app import app
from db import db, Usuario, Parcela, Quiz

class CodeAndCropTestCase(unittest.TestCase):
    
    def setUp(self):
        """Configuración del entorno de pruebas antes de cada test."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Base de datos aislada en memoria
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
            self.seed_test_quizzes()
            
    def tearDown(self):
        """Limpieza de la base de datos después de cada test."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def seed_test_quizzes(self):
        """Siembra un grupo de cuestionario de prueba con la estructura exacta de 3 pasos."""
        q1 = Quiz(
            quiz_group_id=1, step=0, difficulty='easy',
            question='¿Paso 1: Resultado de 10 // 3?', option_a='3.33', option_b='3',
            option_c='1', option_d='0', correct_option='B', hint='División entera'
        )
        q2 = Quiz(
            quiz_group_id=1, step=1, difficulty='easy',
            question='¿Paso 2: Operador de potencia?', option_a='^', option_b='**',
            option_c='exp', option_d='pow', correct_option='B', hint='Dos asteriscos'
        )
        q3 = Quiz(
            quiz_group_id=1, step=2, difficulty='easy',
            question='¿Paso 3: Tipo de dato de 4 / 2?', option_a='int', option_b='float',
            option_c='str', option_d='bool', correct_option='B', hint='Siempre produce float'
        )
        db.session.add_all([q1, q2, q3])
        db.session.commit()

    def login_test_user(self, username="tester_farmer"):
        """Simula el inicio de sesión inyectando el ID del usuario en la sesión de Flask."""
        with app.app_context():
            user = Usuario(username=username, password_hash='dummy_hash')
            db.session.add(user)
            db.session.commit()
            
            # Garantizar la inicialización estricta de sus 64 parcelas relacionales
            from app import ensure_user_plots
            ensure_user_plots(user)
            
            user_id = user.id
            
        with self.app.session_transaction() as sess:
            sess['user_id'] = user_id
            
        return user_id

    # =========================================================================
    # TEST DE ESTRUCTURA: GENERACIÓN COMPLETA DE PARCELAS Y LÍMITES POR NIVEL
    # =========================================================================
    def test_ensure_64_plots_and_level_bounds(self):
        """Verifica que se generen las 64 parcelas físicas y se limite la vista según el nivel."""
        user_id = self.login_test_user()
        
        with app.app_context():
            # Comprobar que en base de datos existan las 64 parcelas del mapa potencial
            db_plots_count = Parcela.query.filter_by(usuario_id=user_id).count()
            self.assertEqual(db_plots_count, 64)
            
        # Consultar el estado del juego mediante la API pública
        response = self.app.get('/api/game/state')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        # Nivel 1 debe retornar un límite máximo de visualización de 16 parcelas (4x4)
        self.assertEqual(data['max_plots'], 16)
        self.assertEqual(data['level'], 1)

    # =========================================================================
    # TEST DE INTERACCIÓN: ARAR, PLANTAR Y VALIDAR PARCELAS BLOQUEADAS
    # =========================================================================
    def test_plot_manual_interaction_flow(self):
        """Prueba el ciclo manual: Arar un terreno 'vacio' -> Cambia a 'dirt' -> Sembrar."""
        self.login_test_user()
        
        # Paso 1: Intentar hacer click en la parcela index 0 (que inicia en estado 'vacio')
        res_click = self.app.post('/api/game/click', 
                                  data=json.dumps({'plot_index': 0, 'action': 'click'}),
                                  content_type='application/json')
        self.assertEqual(res_click.status_code, 200)
        
        # Comprobar en el estado que ahora la parcela está arada ('dirt')
        res_state = self.app.get('/api/game/state')
        data_state = json.loads(res_state.data)
        self.assertEqual(data_state['plots'][0]['cultivo'], 'dirt')
        
        # Paso 2: Intentar plantar en el terreno arado
        res_plant = self.app.post('/api/game/click', 
                                  data=json.dumps({'plot_index': 0, 'action': 'plant'}),
                                  content_type='application/json')
        self.assertEqual(res_plant.status_code, 200)
        
        # Verificar que el cultivo actual sea la semilla activa por defecto ('carrot') en crecimiento
        res_state2 = self.app.get('/api/game/state')
        data_state2 = json.loads(res_state2.data)
        self.assertEqual(data_state2['plots'][0]['cultivo'], 'carrot')
        self.assertEqual(data_state2['plots'][0]['status'], 'growing')

    def test_interaction_out_of_bounds_fails(self):
        """Verifica que un usuario Nivel 1 no pueda interactuar con parcelas superiores a su límite (16)."""
        self.login_test_user()
        
        # Intentar interactuar con la parcela índice 20 estando en Nivel 1 (Límite 16)
        res = self.app.post('/api/game/click', 
                            data=json.dumps({'plot_index': 20, 'action': 'click'}),
                            content_type='application/json')
        
        # Debe ser rechazado por el backend con un código de error de cliente 400
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertIn("Parcela bloqueada o inválida", data['message'])

    # =========================================================================
    # TEST DE AUTOMATIZACIÓN: REGLA DE 4 PARCELAS POR BLOQUE CON RANITAS
    # =========================================================================
    def test_frog_block_automation(self):
        """Valida que una ranita comprada marque como automatizadas exactamente las primeras 4 parcelas (0 a 3)."""
        user_id = self.login_test_user()
        
        with app.app_context():
            user = Usuario.query.get(user_id)
            user.frogs_count = 1  # Forzar la posesión de 1 ranita (Bloque 0: parcelas 0, 1, 2, 3)
            db.session.commit()
            
        res = self.app.get('/api/game/state')
        data = json.loads(res.data)
        
        # Las parcelas del índice 0 al 3 deben figurar como automatizadas = True
        self.assertTrue(data['plots'][0]['automatizada'])
        self.assertTrue(data['plots'][3]['automatizada'])
        
        # La parcela del índice 4 pertenece al Bloque 2, debe figurar como automatizada = False
        self.assertFalse(data['plots'][4]['automatizada'])

    # =========================================================================
    # TEST DE LOGICA DE NEGOCIO: PROGRESIÓN SECUENCIAL DE CUESTIONARIOS
    # =========================================================================
    def test_quiz_sequential_progression_and_rewards(self):
        """Verifica el flujo de respuestas: avanzar pasos 1 y 2, y ganar premios en el paso 3."""
        user_id = self.login_test_user()
        
        # 1. Responder correctamente el Paso 1 (step=0) -> Debe indicar que NO ha completado el grupo completo
        res_step1 = self.app.post('/api/game/answer',
                                  data=json.dumps({'group_id': 1, 'step': 0, 'option': 'B'}),
                                  content_type='application/json')
        data_s1 = json.loads(res_step1.data)
        self.assertTrue(data_s1['correct'])
        self.assertFalse(data_s1['completed'])
        
        # 2. Responder correctamente el Paso 2 (step=1) -> Sigue avanzando de forma modular
        res_step2 = self.app.post('/api/game/answer',
                                  data=json.dumps({'group_id': 1, 'step': 1, 'option': 'B'}),
                                  content_type='application/json')
        data_s2 = json.loads(res_step2.data)
        self.assertTrue(data_s2['correct'])
        self.assertFalse(data_s2['completed'])
        
        # 3. Responder correctamente el Paso 3 (step=2) -> Cuestionario superado. Recompensa otorgada
        res_step3 = self.app.post('/api/game/answer',
                                  data=json.dumps({'group_id': 1, 'step': 2, 'option': 'B'}),
                                  content_type='application/json')
        data_s3 = json.loads(res_step3.data)
        self.assertTrue(data_s3['correct'])
        self.assertTrue(data_s3['completed']) # Completado = True
        self.assertIn("Cuestionario completado con éxito", data_s3['message'])
        
        # 4. Validar impacto persistente en el estado del Agricultor (Oro inicial 100 + Recompensa 500 = 600)
        with app.app_context():
            user = Usuario.query.get(user_id)
            self.assertEqual(user.gold, 600.0)
            self.assertEqual(user.xp, 100)
            # Debe registrar el marcador del cuestionario 1 en su inventario string
            self.assertIn("q_1", user.bought_accessories)

if __name__ == '__main__':
    unittest.main()