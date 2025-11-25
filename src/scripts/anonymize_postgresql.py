"""
Enhanced PostgreSQL anonymization with automatic PII detection
"""

import os
import psycopg2
from typing import Dict, List
from .anonymizer import Anonymizer
from dotenv import load_dotenv

load_dotenv()

class PostgreSQLAnonymizer:
    def __init__(self, sample_size: int = 100):
        """
        Inicializa o anonimizador PostgreSQL
        
        Args:
            sample_size: Número de linhas a amostrar para detecção
        """
        self.sample_size = sample_size
        
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
    
    def get_all_tables(self) -> List[str]:
        """
        Obtém todas as tabelas do banco de dados (exceto tabelas de sistema)
        """
        self.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """
        Obtém todas as colunas de uma tabela
        """
        self.cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s
            AND table_schema = 'public'
        """, (table_name,))
        return [row[0] for row in self.cursor.fetchall()]
    
    def sample_column_data(self, table_name: str, columns: List[str]) -> Dict[str, List[str]]:
        """
        Amostra dados de todas as colunas para análise
        """
        samples = {}
        
        for column in columns:
            try:
                query = f"""
                    SELECT DISTINCT {column} 
                    FROM {table_name} 
                    WHERE {column} IS NOT NULL
                    LIMIT %s
                """
                self.cursor.execute(query, (self.sample_size,))
                samples[column] = [row[0] for row in self.cursor.fetchall()]
            except Exception as e:
                print(f"   ⚠ Erro ao amostrar {column}: {e}")
                samples[column] = []
        
        return samples
    
    def anonymize_all(self):
        """
        Anonimiza automaticamente todas as tabelas detectando PII
        """
        print("🔒 Iniciando anonimização automática PostgreSQL...")
        
        tables = self.get_all_tables()
        print(f"\n📊 Encontradas {len(tables)} tabelas: {', '.join(tables)}")
        
        total_anonymized = 0
        
        for table_name in tables:
            print(f"\n📋 Processando tabela: {table_name}")
            
            # Obter colunas
            columns = self.get_table_columns(table_name)
            print(f"   Colunas: {', '.join(columns)}")
            
            # Amostrar dados
            column_samples = self.sample_column_data(table_name, columns)
            
            # Detectar PII
            pii_columns = self.anonymizer.detect_pii_columns(column_samples)
            
            if not pii_columns:
                print("   ℹ Nenhum PII detectado")
                continue
            
            # Anonimizar cada coluna detectada
            for column_name, pii_type in pii_columns.items():
                count = self._anonymize_column(table_name, column_name, pii_type)
                total_anonymized += count
                print(f"   ✓ {column_name} ({pii_type}): {count} registos anonimizados")
        
        self.conn.commit()
        print(f"\n✅ PostgreSQL anonimizado com sucesso!")
        print(f"📊 Total de campos anonimizados: {total_anonymized}")
        print(f"📊 Estatísticas: {self.anonymizer.get_statistics()}")
    
    def _anonymize_column(self, table_name: str, column_name: str, pii_type: str) -> int:
        """
        Anonimiza uma coluna específica
        """
        # Buscar todos os valores
        self.cursor.execute(
            f"SELECT id, {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
        )
        
        rows = self.cursor.fetchall()
        
        for row_id, original_value in rows:
            # Aplicar estratégia de anonimização
            if pii_type == 'name':
                new_value = self.anonymizer.anonymize_name(original_value)
            elif pii_type == 'email':
                new_value = self.anonymizer.anonymize_email(original_value)
            else:
                continue
            
            # Update na BD
            self.cursor.execute(
                f"UPDATE {table_name} SET {column_name} = %s WHERE id = %s",
                (new_value, row_id)
            )
        
        return len(rows)
    
    def anonymize_text_columns(self):
        """
        Segunda passagem: anonimizar texto livre (campos TEXT que podem conter PII)
        """
        print("\n🔍 Segunda passagem: Detectando PII em campos de texto livre...")
        
        tables = self.get_all_tables()
        
        for table_name in tables:
            # Encontrar colunas TEXT/VARCHAR grandes
            self.cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s
                AND table_schema = 'public'
                AND (data_type = 'text' OR (data_type = 'character varying' AND character_maximum_length > 100))
            """, (table_name,))
            
            text_columns = [row[0] for row in self.cursor.fetchall()]
            
            if not text_columns:
                continue
            
            print(f"\n📋 Analisando texto livre em: {table_name}")
            
            for column in text_columns:
                count = self._anonymize_text_column(table_name, column)
                if count > 0:
                    print(f"   ✓ {column}: {count} registos processados")
        
        self.conn.commit()
    
    def _anonymize_text_column(self, table_name: str, column_name: str) -> int:
        """
        Anonimiza nomes e emails encontrados em campos de texto livre
        """
        self.cursor.execute(
            f"SELECT id, {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL"
        )
        
        rows = self.cursor.fetchall()
        processed = 0
        
        for row_id, original_text in rows:
            if not original_text:
                continue
            
            # Aplicar anonimização de texto
            new_text = self.anonymizer.anonymize_text(original_text)
            
            # Só fazer update se houve mudança
            if new_text != original_text:
                self.cursor.execute(
                    f"UPDATE {table_name} SET {column_name} = %s WHERE id = %s",
                    (new_text, row_id)
                )
                processed += 1
        
        return processed
    
    def print_db(self):
        """
        Da print do conteúdo da base de dados no terminal
        """
        
        tables = self.get_all_tables()
        
        for table_name in tables:
            print(f"\n📋 Tabela: {table_name}")
            columns = self.get_table_columns(table_name)
            print(f"   Colunas: {', '.join(columns)}")
            
            self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = self.cursor.fetchall()
            
            for row in rows:
                print(f"   {row}")
    
    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    anonymizer = PostgreSQLAnonymizer()
    anonymizer.anonymize_all()
    anonymizer.anonymize_text_columns()
    anonymizer.print_db_to_txt()
    anonymizer.close()