"""
Testes para funções utilitárias (base/utils.py)
"""
import unittest
from base.utils import generate_client_hash, generate_product_code, validate_hash


class TestGenerateClientHash(unittest.TestCase):
    """Testes para geração de hash de cliente"""
    
    def test_hash_consistency(self):
        """Testa se o mesmo input gera o mesmo hash"""
        hash1 = generate_client_hash('Cliente ABC')
        hash2 = generate_client_hash('Cliente ABC')
        
        self.assertEqual(hash1, hash2)
    
    def test_hash_format(self):
        """Testa se o hash tem formato MD5 válido (32 caracteres hex)"""
        hash_result = generate_client_hash('Teste')
        
        self.assertEqual(len(hash_result), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash_result))
    
    def test_hash_different_inputs(self):
        """Testa se inputs diferentes geram hashes diferentes"""
        hash1 = generate_client_hash('Cliente A')
        hash2 = generate_client_hash('Cliente B')
        
        self.assertNotEqual(hash1, hash2)
    
    def test_hash_case_insensitive(self):
        """Testa se hash é case-insensitive"""
        hash1 = generate_client_hash('CLIENTE ABC')
        hash2 = generate_client_hash('cliente abc')
        
        self.assertEqual(hash1, hash2)
    
    def test_hash_strips_whitespace(self):
        """Testa se espaços extras são removidos"""
        hash1 = generate_client_hash('  Cliente ABC  ')
        hash2 = generate_client_hash('Cliente ABC')
        
        self.assertEqual(hash1, hash2)
    
    def test_hash_numeric_input(self):
        """Testa com entrada numérica"""
        hash_result = generate_client_hash(12345)
        
        self.assertEqual(len(hash_result), 32)
        self.assertIsInstance(hash_result, str)


class TestGenerateProductCode(unittest.TestCase):
    """Testes para geração de código de produto"""
    
    def test_product_code_format(self):
        """Testa formato do código de produto"""
        code = generate_product_code('PROD123')
        
        self.assertTrue(code.startswith('PROD_'))
        self.assertEqual(code, 'PROD_PROD123')
    
    def test_product_code_numeric(self):
        """Testa com ID numérico"""
        code = generate_product_code(456)
        
        self.assertEqual(code, 'PROD_456')


class TestValidateHash(unittest.TestCase):
    """Testes para validação de hash MD5"""
    
    def test_valid_hash(self):
        """Testa hash válido"""
        valid_hash = 'a' * 32  # 32 caracteres hexadecimais
        self.assertTrue(validate_hash(valid_hash))
    
    def test_invalid_length(self):
        """Testa hash com comprimento inválido"""
        self.assertFalse(validate_hash('abc123'))  # Muito curto
        self.assertFalse(validate_hash('a' * 40))  # Muito longo
    
    def test_invalid_characters(self):
        """Testa hash com caracteres inválidos"""
        self.assertFalse(validate_hash('g' * 32))  # 'g' não é hex
        self.assertFalse(validate_hash('xyz' + 'a' * 29))
    
    def test_none_input(self):
        """Testa com entrada None"""
        self.assertFalse(validate_hash(None))
    
    def test_empty_string(self):
        """Testa com string vazia"""
        self.assertFalse(validate_hash(''))
    
    def test_real_md5_hash(self):
        """Testa com hash MD5 real"""
        real_hash = generate_client_hash('Test Client')
        self.assertTrue(validate_hash(real_hash))


if __name__ == '__main__':
    unittest.main()
