from src.scripts.anonymize_postgresql import PostgreSQLAnonymizer

def test_postgresql_integration():
    """Teste de integração com PostgreSQL real"""
    # Este teste requer docker-compose a correr
    anonymizer = PostgreSQLAnonymizer('config/anonymization_config.yaml')
    
    # Executar anonimização
    anonymizer.anonymize_all()
    
    # Verificar que nomes foram alterados
    anonymizer.cursor.execute("SELECT name FROM users WHERE name = 'João Silva'")
    result = anonymizer.cursor.fetchone()
    
    assert result is None  # Nome original não deve existir
    
    anonymizer.close()