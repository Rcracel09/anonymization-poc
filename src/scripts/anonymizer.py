"""
Core anonymization logic usando spaCy + Faker
"""

import spacy
from faker import Faker
from typing import Dict, Optional

class Anonymizer:
    def __init__(self, locale: str = 'pt_PT'):
        """
        Inicializa o anonimizador com modelo spaCy português
        """
        print("📦 Carregando modelo spaCy português...")
        self.nlp = spacy.load("pt_core_news_lg")
        self.fake = Faker(locale)
        
        # Dicionário para consistência
        # Garante que "João Silva" vira sempre o mesmo nome fake
        self.name_mapping: Dict[str, str] = {}
        self.email_mapping: Dict[str, str] = {}
    
    def anonymize_name(self, original_name: str) -> str:
        """
        Anonimiza um nome, mantendo consistência
        """
        if not original_name or original_name.strip() == "":
            return original_name
        
        if original_name not in self.name_mapping:
            self.name_mapping[original_name] = self.fake.name()
        
        return self.name_mapping[original_name]
    
    def anonymize_email(self, original_email: str) -> str:
        """
        Anonimiza um email
        """
        if not original_email or '@' not in original_email:
            return original_email
        
        if original_email not in self.email_mapping:
            self.email_mapping[original_email] = self.fake.email()
        
        return self.email_mapping[original_email]
    
    def anonymize_text(self, text: str) -> str:
        """
        Usa spaCy para detetar e anonimizar nomes em texto livre
        """
        if not text or text.strip() == "":
            return text
        
        doc = self.nlp(text)
        anonymized_text = text

        
        # Processar entidades de trás para frente para não quebrar offsets
        for ent in reversed(doc.ents):
            if ent.label_ == "PER":  # Nome de pessoa
                original = ent.text
                anonymized = self.anonymize_name(original)
                
                # Substituir no texto
                start = ent.start_char
                end = ent.end_char
                anonymized_text = (
                    anonymized_text[:start] + 
                    anonymized + 
                    anonymized_text[end:]
                )
        
        return anonymized_text
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas da anonimização
        """
        return {
            'total_names_anonymized': len(self.name_mapping),
            'total_emails_anonymized': len(self.email_mapping),
            'sample_mappings': {
                'names': dict(list(self.name_mapping.items())[:5]),
                'emails': dict(list(self.email_mapping.items())[:3])
            }
        }