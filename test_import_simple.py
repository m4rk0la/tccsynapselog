import sys
print("Python path:", sys.path[:3])

try:
    import ml.client_scoring as cs
    print(f"✅ Módulo importado: {cs}")
    print(f"✅ Atributos do módulo: {[x for x in dir(cs) if not x.startswith('_')]}")
    
    if hasattr(cs, 'calcular_scores_para_usuario'):
        print("✅ Função 'calcular_scores_para_usuario' existe!")
    else:
        print("❌ Função 'calcular_scores_para_usuario' NÃO encontrada")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
