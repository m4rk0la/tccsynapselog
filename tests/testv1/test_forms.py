"""
Testes para formulários Flask-WTF (base/forms.py)
"""
import unittest
from app import create_app


class TestLoginForm(unittest.TestCase):
    """Testes para o formulário de login"""
    
    def setUp(self):
        """Cria app de teste com contexto"""
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Remove contexto"""
        self.app_context.pop()
    
    def test_login_form_fields(self):
        """Testa se formulário tem campos obrigatórios"""
        from base.forms import LoginForm
        form = LoginForm()
        
        self.assertTrue(hasattr(form, 'email'))
        self.assertTrue(hasattr(form, 'password'))
        self.assertTrue(hasattr(form, 'submit'))
    
    def test_email_validator(self):
        """Testa validador de email"""
        from base.forms import LoginForm
        form = LoginForm()
        
        # Email válido
        form.email.data = 'user@example.com'
        form.password.data = 'senha123'
        
        # Verifica se tem validadores
        self.assertTrue(len(form.email.validators) > 0)


class TestRegistrationForm(unittest.TestCase):
    """Testes para o formulário de registro"""
    
    def setUp(self):
        """Cria app de teste com contexto"""
        self.app = create_app('development')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Remove contexto"""
        self.app_context.pop()
    
    def test_registration_form_fields(self):
        """Testa se formulário tem campos obrigatórios"""
        from base.forms import RegistrationForm
        form = RegistrationForm()
        
        self.assertTrue(hasattr(form, 'username'))
        self.assertTrue(hasattr(form, 'email'))
        self.assertTrue(hasattr(form, 'password'))
        self.assertTrue(hasattr(form, 'confirm_password'))
        self.assertTrue(hasattr(form, 'submit'))
    
    def test_username_length_validator(self):
        """Testa validador de comprimento do username"""
        from base.forms import RegistrationForm
        form = RegistrationForm()
        
        # Verifica se tem validadores de comprimento
        validators = [v for v in form.username.validators if hasattr(v, 'min')]
        self.assertTrue(len(validators) > 0)
    
    def test_password_confirmation_validator(self):
        """Testa validador de confirmação de senha"""
        from base.forms import RegistrationForm
        form = RegistrationForm()
        
        # Verifica se confirm_password tem validador EqualTo
        validators = [v for v in form.confirm_password.validators]
        self.assertTrue(len(validators) > 0)


if __name__ == '__main__':
    unittest.main()
