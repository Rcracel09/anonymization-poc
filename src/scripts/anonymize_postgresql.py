"""
Anonimização específica para PostgreSQL
"""

import os
import psycopg2 # type: ignore
import yaml
from .anonymizer import Anonymizer
from dotenv import load_dotenv # type: ignore


load_dotenv()

class PostgreSQLAnonymizer:
    def __init__(self, config_path: str):
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.config = config['postgresql']
        
        # Inicializar anonimizador
        self.anonymizer = Anonymizer(locale='pt_PT')
        
        # Conectar à BD
        self.conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        self.cursor = self.conn.cursor()
    
    def anonymize_all(self):
        """
        Anonimiza todas as tabelas configuradas
        """
        print("🔒 Iniciando anonimização PostgreSQL...")
        
        for table_name, table_config in self.config['tables'].items():
            print(f"\n📋 Processando tabela: {table_name}")
            self._anonymize_table(table_name, table_config['columns'])
        
        self.conn.commit()
        print("\n✅ PostgreSQL anonimizado com sucesso!")
        print(f"📊 Estatísticas: {self.anonymizer.get_statistics()}")
    
    def _anonymize_table(self, table_name: str, columns: list):
        """
        Anonimiza uma tabela específica
        """
        for column_config in columns:
            column_name = column_config['name']
            strategy = column_config['strategy']
            col_type = column_config['type']
            
            print(f"  └─ Coluna: {column_name} ({strategy})")
            
            # Buscar todos os registos
            self.cursor.execute(
                f"SELECT id, {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
            )
            
            rows = self.cursor.fetchall()
            
            for row_id, original_value in rows:
                # Aplicar estratégia de anonimização
                if strategy == 'faker':
                    if col_type == 'full_name':
                        new_value = self.anonymizer.anonymize_name(original_value)
                    elif col_type == 'email':
                        new_value = self.anonymizer.anonymize_email(original_value)
                    else:
                        continue
                
                elif strategy == 'spacy':
                    new_value = self.anonymizer.anonymize_text(original_value)
                
                else:
                    continue
                
                # Update na BD
                self.cursor.execute(
                    f"UPDATE {table_name} SET {column_name} = %s WHERE id = %s",
                    (new_value, row_id)
                )
            
            print(f"     ✓ {len(rows)} registos anonimizados")
    
    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    anonymizer = PostgreSQLAnonymizer('config/anonymization_config.yaml')
    anonymizer.anonymize_all()
    anonymizer.close()