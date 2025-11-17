"""
Anonimização específica para MongoDB
"""

import os
from pymongo import MongoClient # type: ignore
import yaml
from .anonymizer import Anonymizer
from dotenv import load_dotenv # type: ignore

load_dotenv()

class MongoDBAnonymizer:
    def __init__(self, config_path: str):
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.config = config['mongodb']
        
        # Inicializar anonimizador
        self.anonymizer = Anonymizer(locale='pt_PT')
        
        # Conectar ao MongoDB
        mongo_uri = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}"
        self.client = MongoClient(mongo_uri)
        self.db = self.client[os.getenv('MONGO_DB')]
    
    def anonymize_all(self):
        """
        Anonimiza todas as coleções configuradas
        """
        print("🔒 Iniciando anonimização MongoDB...")
        
        for collection_name, collection_config in self.config['collections'].items():
            print(f"\n📋 Processando coleção: {collection_name}")
            self._anonymize_collection(collection_name, collection_config['fields'])
        
        print("\n✅ MongoDB anonimizado com sucesso!")
        print(f"📊 Estatísticas: {self.anonymizer.get_statistics()}")
    
    def _anonymize_collection(self, collection_name: str, fields: list):
        """
        Anonimiza uma coleção específica
        """
        collection = self.db[collection_name]
        
        for field_config in fields:
            field_name = field_config['name']
            strategy = field_config['strategy']
            field_type = field_config['type']
            
            print(f"  └─ Campo: {field_name} ({strategy})")
            
            # Buscar documentos
            query = {field_name: {"$exists": True, "$ne": None}}
            documents = list(collection.find(query))
            
            for doc in documents:
                # Obter valor (suporta nested fields como "metadata.reviewer")
                value = self._get_nested_field(doc, field_name)
                
                if not value:
                    continue
                
                # Aplicar estratégia
                if strategy == 'faker':
                    if field_type == 'full_name':
                        new_value = self.anonymizer.anonymize_name(value)
                    elif field_type == 'email':
                        new_value = self.anonymizer.anonymize_email(value)
                    else:
                        continue
                
                elif strategy == 'spacy':
                    new_value = self.anonymizer.anonymize_text(value)
                
                else:
                    continue
                
                # Update no MongoDB
                self._set_nested_field(doc, field_name, new_value)
                collection.replace_one({'_id': doc['_id']}, doc)
            
            print(f"     ✓ {len(documents)} documentos anonimizados")
    
    def _get_nested_field(self, doc: dict, field_path: str):
        """Obter valor de campo nested (ex: metadata.reviewer)"""
        keys = field_path.split('.')
        value = doc
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def _set_nested_field(self, doc: dict, field_path: str, value):
        """Definir valor de campo nested"""
        keys = field_path.split('.')
        current = doc
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def close(self):
        self.client.close()

if __name__ == "__main__":
    anonymizer = MongoDBAnonymizer('config/anonymization_config.yaml')
    anonymizer.anonymize_all()
    anonymizer.close()