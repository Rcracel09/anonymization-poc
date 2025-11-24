"""
Enhanced anonymization logic with automatic detection of PII
Uses spaCy + Faker + Regex to detect and anonymize emails and names
"""

import spacy
import re
from faker import Faker
from typing import Dict, Optional, List, Tuple

class Anonymizer:
    def __init__(self, locale: str = 'pt_PT'):
        """
        Inicializa o anonimizador com modelo spaCy português
        """
        print("📦 Carregando modelo spaCy português...")
        self.nlp = spacy.load("pt_core_news_lg")
        self.fake = Faker(locale)
        
        # Dicionário para consistência
        self.name_mapping: Dict[str, str] = {}
        self.email_mapping: Dict[str, str] = {}
        
        # Padrões regex para detecção
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # Palavras-chave para identificar colunas de email
        self.email_keywords = ['email', 'e-mail', 'mail', 'correo', 'correio']
        
        # Palavras-chave para identificar colunas de nome
        self.name_keywords = [
            'name', 'nome', 'namen', 'nombre',
            'first_name', 'last_name', 'full_name',
            'firstname', 'lastname', 'fullname',
            'author', 'autor', 'creator', 'criador',
            'owner', 'proprietario', 'user', 'usuario',
            'reviewer', 'revisor', 'approver', 'aprovador',
            'contact', 'contato', 'person', 'pessoa',
            'client', 'cliente', 'customer'
        ]
    
    def is_email_column(self, column_name: str, sample_values: List[str]) -> bool:
        """
        Detecta se uma coluna contém emails
        """
        # Verificar nome da coluna
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in self.email_keywords):
            return True
        
        # Verificar valores de amostra
        if sample_values:
            email_count = sum(1 for val in sample_values if val and self.email_pattern.match(str(val)))
            # Se >50% dos valores são emails, é uma coluna de email
            return email_count / len(sample_values) > 0.5
        
        return False
    
    def is_name_column(self, column_name: str, sample_values: List[str]) -> bool:
        """
        Detecta se uma coluna contém nomes de pessoas
        """
        
        # Usar spaCy para analisar valores de amostra
        if sample_values:
            person_count = 0
            for val in sample_values[:10]:  
                if not val or not isinstance(val, str):
                    continue
                
                doc = self.nlp(val.strip())
                
                # Verificar se o valor inteiro é uma entidade PERSON
                if len(doc.ents) > 0:
                    for ent in doc.ents:
                        if ent.label_ == "PER":
                            person_count += 1
                            break
                        
                # No caso de nao encontrar entidade, usar heurística simples
                elif self._looks_like_name(val):
                    person_count += 1
            
            # Se >40% parecem nomes, é uma coluna de nome
            flag = person_count / min(len(sample_values), 10) > 0.4
        
        # Verificar nome da coluna
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in self.name_keywords):
            return True and flag

        return flag
    
    def _looks_like_name(self, text: str) -> bool:
        """
        Verifica se um texto parece um nome (heurística simples)
        """
        if not text or len(text) < 3:
            return False
        
        # Nome típico: 2-4 palavras capitalizadas
        words = text.split()
        if len(words) > 5 or len(words) == 0:
            return False
        
        capitalized_words = sum(1 for w in words if w and w[0].isupper())
        
        # Pelo menos 50% das palavras capitalizadas
        return capitalized_words / len(words) >= 0.5
    
    def detect_pii_columns(self, column_samples: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Detecta automaticamente colunas com PII
        Retorna: {column_name: 'email' ou 'name'}
        """
        pii_columns = {}
        
        print("\n🔍 Detectando colunas com PII...")
        
        for column_name, sample_values in column_samples.items():
            # Filtrar valores NULL
            sample_values = [v for v in sample_values if v is not None]
            
            if not sample_values:
                continue
            
            # Testar se é email
            if self.is_email_column(column_name, sample_values):
                pii_columns[column_name] = 'email'
                print(f"   ✓ {column_name} → EMAIL")
                continue
            
            # Testar se é nome
            if self.is_name_column(column_name, sample_values):
                pii_columns[column_name] = 'name'
                print(f"   ✓ {column_name} → NAME")
                continue
        
        return pii_columns
    
    def anonymize_name(self, original_name: str) -> str:
        """
        Anonimiza um nome, mantendo consistência
        """
        if not original_name or str(original_name).strip() == "":
            return original_name
        
        name_str = str(original_name)
        
        if name_str not in self.name_mapping:
            self.name_mapping[name_str] = self.fake.name()
        
        return self.name_mapping[name_str]
    
    def anonymize_email(self, original_email: str) -> str:
        """
        Anonimiza um email
        """
        if not original_email or '@' not in str(original_email):
            return original_email
        
        email_str = str(original_email)
        
        if email_str not in self.email_mapping:
            self.email_mapping[email_str] = self.fake.email()
        
        return self.email_mapping[email_str]
    
    def anonymize_text(self, text: str) -> str:
        """
        Usa spaCy para detectar e anonimizar nomes e emails em texto livre
        """
        if not text or str(text).strip() == "":
            return text
        
        text_str = str(text)
        
        # Primeiro, anonimizar emails com regex
        anonymized_text = text_str
        for email_match in self.email_pattern.finditer(text_str):
            original_email = email_match.group()
            anonymized_email = self.anonymize_email(original_email)
            anonymized_text = anonymized_text.replace(original_email, anonymized_email)
        
        # Depois, usar spaCy para nomes
        doc = self.nlp(anonymized_text)
        
        # Processar entidades de trás para frente para não quebrar offsets
        for ent in reversed(doc.ents):
            if ent.label_ == "PER":  
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
        return {
            'total_names_anonymized': len(self.name_mapping),
            'total_emails_anonymized': len(self.email_mapping),
            'sample_mappings': {
                'names': dict(list(self.name_mapping.items())[:5]),
                'emails': dict(list(self.email_mapping.items())[:3])
            }
        }