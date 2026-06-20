import unittest
import os
import datetime
from app import app, db, Usuario, Parcela, Quiz, process_growth_sync
class CodeAndCropTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app_client = app.test_client()
        
        with app.app_context():
            db.create_all()
            # Seed quiz bank
            from db import seed_quizzes
            seed_quizzes()
            
            # Create a test user
            self.test_user = Usuario(username="TestFarmer")
            self.test_user.set_password("secret123")
            self.test_user.gold = 100.0
            db.session.add(self.test_user)
            db.session.commit()
            
            # Verify and create user plots
            from app import ensure_user_plots
            ensure_user_plots(self.test_user)
    def tearDown(self):
        with app.app_context():
            db.drop_all()
    def test_quiz_seeding(self):
        with app.app_context():
            quizzes_count = Quiz.query.count()
            self.assertGreater(quizzes_count, 0)
            
            # Retrieve a quiz and make sure the correct option is loaded
            py_quiz = Quiz.query.filter_by(language="Python").first()
            self.assertIsNotNone(py_quiz)
            self.assertIn(py_quiz.correct_option, ['A', 'B', 'C', 'D'])
    def test_ensure_user_plots(self):
        with app.app_context():
            u = Usuario.query.filter_by(username="TestFarmer").first()
            self.assertEqual(len(u.parcelas), 64)
            # Verify coordinates
            p_0 = Parcela.query.filter_by(usuario_id=u.id, plot_index=0).first()
            self.assertEqual(p_0.posicion_x, 0)
            self.assertEqual(p_0.posicion_y, 0)
    def test_manual_grow_sync(self):
        with app.app_context():
            u = Usuario.query.filter_by(username="TestFarmer").first()
            # Set a plot to manual growing carrot
            p = Parcela.query.filter_by(usuario_id=u.id, plot_index=5).first()
            p.cultivo = 'carrot'
            p.status = 'growing'
            p.grow_progress = 0.0
            
            # Backdate last_sync to 4 seconds ago
            u.last_sync = datetime.datetime.utcnow() - datetime.timedelta(seconds=4)
            db.session.commit()
            
            # Sync
            passive_gained = process_growth_sync(u)
            
            # Verify progress incremented (Carrot grow time is 8s, so 4s elapsed should be 50.0%)
            self.assertEqual(passive_gained, 0.0) # no passive gain from manual plot
            self.assertAlmostEqual(p.grow_progress, 50.0, places=1)
            self.assertEqual(p.status, 'growing')
    def test_automated_grow_sync(self):
        with app.app_context():
            u = Usuario.query.filter_by(username="TestFarmer").first()
            
            # Automate plot 10 with carrot
            p = Parcela.query.filter_by(usuario_id=u.id, plot_index=10).first()
            p.cultivo = 'carrot'
            p.status = 'growing'
            p.grow_progress = 0.0
            p.automatizada = True
            
            # Backdate last_sync to 12 seconds ago (Carrot takes 8s, so 1 cycle completed)
            u.last_sync = datetime.datetime.utcnow() - datetime.timedelta(seconds=12)
            db.session.commit()
            
            # Sync
            passive_gained = process_growth_sync(u)
            
            # Verify cycle completion (1 cycle completed, 4s remaining -> 50% progress)
            # Python multiplier is 1.0, Carrot value is 10.0
            self.assertEqual(passive_gained, 10.0)
            self.assertEqual(u.gold, 110.0)
            self.assertAlmostEqual(p.grow_progress, 50.0, places=1)
    def test_prestige_reset_transaction(self):
        with app.app_context():
            u = Usuario.query.filter_by(username="TestFarmer").first()
            u.gold = 4000.0 # Cost of SQL is 5000.0
            db.session.commit()
            
            # Attempt prestige buy - should fail due to gold constraint
            with self.app_client.session_transaction() as sess:
                sess['user_id'] = u.id
                
            response = self.app_client.post('/api/game/shop/buy_language', json={"language": "SQL"})
            self.assertEqual(response.status_code, 400)
            
            # Ensure stats were NOT modified (Atomic Transaction Safety)
            u_check = Usuario.query.filter_by(username="TestFarmer").first()
            self.assertEqual(u_check.gold, 4000.0)
            self.assertEqual(u_check.active_language, "Python")
if __name__ == '__main__':
    unittest.main()
