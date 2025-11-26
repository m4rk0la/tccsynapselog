"""Script para verificar e configurar senha do usuário admin"""
from app import create_app
from base.models import db, User

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("🔐 VERIFICAÇÃO DE SENHA DO USUÁRIO")
    print("="*80 + "\n")
    
    # Busca usuário admin
    user = User.query.filter_by(email='admin@synapselLog.com').first()
    
    if not user:
        print("❌ Usuário admin@synapselLog.com não encontrado!")
        print("\nCriando usuário admin...")
        
        user = User(
            username='admin',
            email='admin@synapselLog.com',
            role='admin',
            is_active=True
        )
        user.set_password('admin123')  # Senha padrão: admin123
        
        db.session.add(user)
        db.session.commit()
        
        print("✅ Usuário criado com sucesso!")
        print(f"   Email: admin@synapselLog.com")
        print(f"   Senha: admin123")
    else:
        print(f"✅ Usuário encontrado:")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Role: {user.role}")
        print(f"   Ativo: {user.is_active}")
        print(f"   Password Hash: {user.password_hash[:30]}...")
        
        # Testa se tem senha configurada
        if user.password_hash:
            print("\n🔑 Testando senhas comuns...")
            
            senhas_teste = ['admin', 'admin123', '123456', 'password']
            senha_encontrada = False
            
            for senha in senhas_teste:
                if user.check_password(senha):
                    print(f"   ✅ Senha encontrada: '{senha}'")
                    senha_encontrada = True
                    break
            
            if not senha_encontrada:
                print("   ❌ Nenhuma senha comum funcionou")
                print("\n💡 Deseja redefinir a senha para 'admin123'? (s/n)")
                resposta = input("   >>> ")
                
                if resposta.lower() == 's':
                    user.set_password('admin123')
                    db.session.commit()
                    print("   ✅ Senha redefinida para: admin123")
        else:
            print("\n⚠️ Usuário sem senha configurada!")
            print("   Definindo senha padrão: admin123")
            user.set_password('admin123')
            db.session.commit()
            print("   ✅ Senha configurada!")
    
    print("\n" + "="*80)
    print("📋 CREDENCIAIS DE LOGIN")
    print("="*80)
    print(f"   Email: admin@synapselLog.com")
    print(f"   Senha: admin123")
    print("="*80 + "\n")
